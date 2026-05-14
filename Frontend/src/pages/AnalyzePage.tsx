import { useCallback, useEffect, useRef, useState } from "react"
import { ErrorState } from "../components/ErrorState"
import { ImageUploader } from "../components/ImageUploader"
import { ResultCard } from "../components/ResultCard"
import { SafetyBanner } from "../components/SafetyBanner"
import { fileToVisionDataUrl, generate } from "../lib/api"
import type { GenerateResponse } from "../lib/types"

type SubmitState = "idle" | "submitting" | "success" | "error"

export function AnalyzePage() {
  const [file, setFile] = useState<File | null>(null)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [question, setQuestion] = useState("")
  const [state, setState] = useState<SubmitState>("idle")
  const [result, setResult] = useState<GenerateResponse | null>(null)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  // Ref tracks the current object URL so unmount cleanup is always accurate,
  // even if state has been updated since the URL was created.
  const currentUrlRef = useRef<string | null>(null)

  const pickFile = useCallback((next: File) => {
    if (currentUrlRef.current) URL.revokeObjectURL(currentUrlRef.current)
    const url = URL.createObjectURL(next)
    currentUrlRef.current = url
    setFile(next)
    setPreviewUrl(url)
    setState("idle")
    setErrorMessage(null)
  }, [])

  const clearFile = useCallback(() => {
    if (currentUrlRef.current) URL.revokeObjectURL(currentUrlRef.current)
    currentUrlRef.current = null
    setFile(null)
    setPreviewUrl(null)
    setState("idle")
    setErrorMessage(null)
  }, [])

  useEffect(() => {
    // Revoke any outstanding object URL when the page unmounts.
    return () => {
      if (currentUrlRef.current) {
        URL.revokeObjectURL(currentUrlRef.current)
        currentUrlRef.current = null
      }
    }
  }, [])

  async function onAnalyze() {
    if (!file || !question.trim()) return
    setState("submitting")
    setResult(null)
    setErrorMessage(null)
    try {
      const dataUrl = await fileToVisionDataUrl(file)
      const res = await generate(question, { images: [dataUrl] })
      setResult(res)
      setState("success")
    } catch (e) {
      setErrorMessage(e instanceof Error ? e.message : "Request failed.")
      setState("error")
    }
  }

  return (
    <div className="mx-auto flex w-full max-w-3xl flex-col gap-3 px-3 py-4 2xl:gap-4 2xl:px-4 2xl:py-6">
      <header>
        <h1 className="text-xl font-semibold text-brand-text">Analyze a photo</h1>
        <p className="text-xs text-brand-text-muted">
          Upload an engine-bay photo and ask a question about it.
        </p>
      </header>

      <ImageUploader onPick={pickFile} disabled={state === "submitting"} />

      {previewUrl && (
        <div className="flex items-center gap-3 rounded-xl border border-brand-border bg-brand-card/40 backdrop-blur p-3">
          <img
            src={previewUrl}
            alt="Selected"
            className="h-20 w-28 rounded-lg object-cover"
          />
          <div className="flex-1 text-xs text-brand-text-muted">
            <p className="font-medium text-brand-text">{file?.name}</p>
            <p>
              {file && `${(file.size / 1024).toFixed(0)} KB · ${file.type}`}
            </p>
          </div>
          <button
            type="button"
            onClick={clearFile}
            aria-label="Remove attachment"
            className="inline-flex items-center gap-1.5 rounded-lg border border-brand-border bg-brand-card px-3 py-2 text-xs font-medium text-brand-text-muted transition-colors hover:cursor-pointer hover:border-brand-accent hover:bg-brand-card-soft hover:text-brand-text"
          >
            Remove
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="14"
              height="14"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
            >
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>
      )}

      <textarea
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        placeholder="What part is this and where do I put oil?"
        rows={3}
        className="rounded-xl border border-brand-border bg-brand-card px-3.5 py-2.5 2xl:px-4 2xl:py-3 text-sm text-brand-text placeholder:text-brand-text-muted/60 outline-none transition-colors focus:border-brand-accent disabled:opacity-60"
        disabled={state === "submitting"}
      />

      <button
        type="button"
        onClick={onAnalyze}
        disabled={!file || !question.trim() || state === "submitting"}
        className="self-start rounded-xl bg-brand-accent px-5 py-2.5 2xl:px-6 2xl:py-3 text-sm font-semibold text-white shadow-sm transition-colors hover:cursor-pointer hover:bg-brand-glow-soft disabled:cursor-not-allowed disabled:bg-brand-card-soft disabled:text-brand-text-muted disabled:shadow-none disabled:hover:bg-brand-card-soft"
      >
        {state === "submitting" ? "Analyzing…" : "Analyze"}
      </button>

      {state === "success" && result && (
        <>
          <SafetyBanner variant="verify">
            AI answers can be wrong — double-check critical repairs with a professional.
          </SafetyBanner>
          <ResultCard
            thumbnailUrl={previewUrl ?? undefined}
            identifiedPart="Photo analysis"
            explanation={result.content}
            nextStep={`Model: ${result.model} · est. $${result.cost_usd.toFixed(4)} · ${result.latency_ms} ms`}
            safetyNote="When in doubt, verify with your owner's manual or a qualified mechanic."
          />
        </>
      )}

      {state === "error" && (
        <ErrorState
          message={
            errorMessage ??
            "We couldn't process that image. Try a JPEG or PNG, or a smaller file."
          }
        />
      )}
    </div>
  )
}
