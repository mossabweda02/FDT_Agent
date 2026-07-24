import { useCallback, useEffect, useRef, useState } from "react";

export default function useSmartAutoScroll(dependencies = []) {
  const containerRef = useRef(null);
  const [isNearBottom, setIsNearBottom] = useState(true);

  const checkIsNearBottom = useCallback(() => {
    const el = containerRef.current;
    if (!el) return true;

    const distanceFromBottom =
      el.scrollHeight - el.scrollTop - el.clientHeight;

    return distanceFromBottom < 120;
  }, []);

  const handleScroll = useCallback(() => {
    setIsNearBottom(checkIsNearBottom());
  }, [checkIsNearBottom]);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;

    el.addEventListener("scroll", handleScroll);
    return () => el.removeEventListener("scroll", handleScroll);
  }, [handleScroll]);

  useEffect(() => {
    const el = containerRef.current;
    if (!el || !isNearBottom) return;

    requestAnimationFrame(() => {
      el.scrollTo({
        top: el.scrollHeight,
        behavior: "smooth",
      });
    });
  }, dependencies);

  const scrollToBottom = useCallback(() => {
    const el = containerRef.current;
    if (!el) return;

    el.scrollTo({
      top: el.scrollHeight,
      behavior: "smooth",
    });
  }, []);

  return {
    containerRef,
    isNearBottom,
    scrollToBottom,
  };
}