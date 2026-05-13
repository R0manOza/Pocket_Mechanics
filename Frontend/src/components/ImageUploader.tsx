import { useCallback, useRef, useState } from "react"

const MAX_BYTES = 5 * 1024 * 1024 // 5 MB
const ACCEPT = "image/*"

interface Props {
  onPick: (file: File) => void
  disabled?: boolean
}

export function ImageUploader({ onPick, disabled }: Props) {
  const inputRef = useRef<HTMLInputElement | null>(null)
  const [dragOver, setDragOver] = useState(false)
  const [pickerError, setPickerError] = useState<string | null>(null)

  const accept = useCallback(
    (file: File) => {
      if (!file.type.startsWith("image/")) {
        setPickerError("Please choose an image file (JPG, PNG, HEIC, …).")
        return
      }
      if (file.size > MAX_BYTES) {
        setPickerError("That image is over 5 MB — try a smaller photo.")
        return
      }
      setPickerError(null)
      onPick(file)
    },
    [onPick],
  )

  return (
    <div className="flex flex-col gap-2">
      <button
        type="button"
        disabled={disabled}
        onClick={() => inputRef.current?.click()}
        onDragOver={(e) => {
          e.preventDefault()
          if (!disabled) setDragOver(true)
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={(e) => {
          e.preventDefault()
          setDragOver(false)
          const file = e.dataTransfer.files?.[0]
          if (file) accept(file)
        }}
        className={`flex h-44 w-full flex-col items-center justify-center gap-2 rounded-2xl border-2 border-dashed text-sm transition ${
          disabled
            ? "cursor-not-allowed border-slate-200 bg-slate-50 text-slate-400"
            : dragOver
              ? "border-slate-900 bg-slate-100 text-slate-800"
              : "border-slate-300 bg-white text-slate-600 hover:border-slate-500 hover:text-slate-800"
        }`}
      >
        <span className="text-base font-medium">Drop an engine-bay photo</span>
        <span className="text-xs">or click to choose · JPG/PNG · up to 5 MB</span>
      </button>
      <input
        ref={inputRef}
        type="file"
        accept={ACCEPT}
        className="hidden"
        onChange={(e) => {
          const file = e.target.files?.[0]
          if (file) accept(file)
          e.target.value = ""
        }}
      />
      {pickerError && (
        <p className="text-xs text-amber-700">{pickerError}</p>
      )}
    </div>
  )
}
