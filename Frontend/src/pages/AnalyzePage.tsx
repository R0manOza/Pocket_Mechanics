import { useCallback, useEffect, useRef, useState } from "react"
import { ErrorState } from "../components/ErrorState"
import { ImageUploader } from "../components/ImageUploader"
import { ResultCard } from "../components/ResultCard"
import { SafetyBanner } from "../components/SafetyBanner"

type SubmitState = "idle" | "submitting" | "coming_soon" | "error"

export function AnalyzePage() {
  const [file, setFile] = useState<File | null>(null)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [question, setQuestion] = useState("")
  const [state, setState] = useState<SubmitState>("idle")

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
  }, [])

  const clearFile = useCallback(() => {
    if (currentUrlRef.current) URL.revokeObjectURL(currentUrlRef.current)
    currentUrlRef.current = null
    setFile(null)
    setPreviewUrl(null)
    setState("idle")
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

  function onAnalyze() {
    if (!file || !question.trim()) return
    setState("submitting")
    // The vision endpoint POST /api/ai/analyze does not exist yet.
    // Surface a friendly "coming soon" state so the UI is reviewable end-to-end
    // and the call site is a one-line swap once the backend ships.
    window.setTimeout(() => setState("coming_soon"), 350)
  }

  return (
    <div className="mx-auto flex w-full max-w-3xl flex-col gap-4 px-4 py-6">
      <header>
        <h1 className="text-xl font-semibold text-slate-900">Analyze a photo</h1>
        <p className="text-xs text-slate-500">
          Upload an engine-bay photo and ask a question about it.
        </p>
      </header>

      <ImageUploader onPick={pickFile} disabled={state === "submitting"} />

      {previewUrl && (
        <div className="flex items-center gap-3 rounded-xl border border-slate-200 bg-white p-3">
          <img
            src={previewUrl}
            alt="Selected"
            className="h-20 w-28 rounded-lg object-cover"
          />
          <div className="flex-1 text-xs text-slate-600">
            <p className="font-medium text-slate-800">{file?.name}</p>
            <p>
              {file && `${(file.size / 1024).toFixed(0)} KB · ${file.type}`}
            </p>
          </div>
          <button
            type="button"
            onClick={clearFile}
            className="rounded-lg border border-slate-200 bg-white px-2.5 py-1 text-xs text-slate-600 hover:bg-slate-50"
          >
            Remove
          </button>
        </div>
      )}

      <textarea
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        placeholder="What part is this and where do I put oil?"
        rows={3}
        className="rounded-xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 outline-none focus:border-slate-500"
        disabled={state === "submitting"}
      />

      <button
        type="button"
        onClick={onAnalyze}
        disabled={!file || !question.trim() || state === "submitting"}
        className="self-start rounded-xl bg-slate-900 px-4 py-3 text-sm font-medium text-white disabled:cursor-not-allowed disabled:bg-slate-400"
      >
        {state === "submitting" ? "Analyzing…" : "Analyze"}
      </button>

      {state === "coming_soon" && (
        <>
          <SafetyBanner variant="verify">
            The vision endpoint isn't live yet — this page is wired and ready for{" "}
            <code>POST /api/ai/analyze</code> the moment it ships.
          </SafetyBanner>
          <ResultCard
            thumbnailUrl={previewUrl ?? undefined}
            identifiedPart="Vision endpoint coming soon"
            explanation="Until the backend ships POST /api/ai/analyze, the result card here is a preview of how identification, explanation, next steps, and safety notes will render."
            nextStep="Until then, ask the same question in the Chat tab and the text-only assistant will help."
            safetyNote="When in doubt, verify with your owner's manual or a qualified mechanic."
          />
        </>
      )}

      {state === "error" && (
        <ErrorState message="We couldn't process that image. Please try a different photo." />
      )}
    </div>
  )
}
