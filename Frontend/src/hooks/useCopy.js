import { useCallback, useState } from "react";

export default function useCopy() {
  const [copied, setCopied] = useState(false);

  const copy = useCallback(async (text) => {
    try {
      await navigator.clipboard.writeText(text);

      setCopied(true);

      setTimeout(() => {
        setCopied(false);
      }, 2000);
    } catch (error) {
      console.error("Unable to copy to clipboard.", error);
    }
  }, []);

  return [copied, copy];
}