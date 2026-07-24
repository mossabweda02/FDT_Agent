import { useEffect, useState } from "react";
import { fetchMyProfilePhoto } from "../api/graphApi";

export default function useMicrosoftProfilePhoto(enabled = true) {
  const [photoUrl, setPhotoUrl] = useState(null);
  const [loading, setLoading] = useState(Boolean(enabled));
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!enabled) return;

    let mounted = true;
    let objectUrl = null;

    async function loadPhoto() {
      try {
        setLoading(true);
        setError(null);

        objectUrl = await fetchMyProfilePhoto();

        if (mounted) {
          setPhotoUrl(objectUrl);
        }
      } catch (err) {
        if (mounted) {
          setError(err);
          setPhotoUrl(null);
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    }

    loadPhoto();

    return () => {
      mounted = false;

      if (objectUrl) {
        URL.revokeObjectURL(objectUrl);
      }
    };
  }, [enabled]);

  return {
    photoUrl,
    loading,
    error,
  };
}