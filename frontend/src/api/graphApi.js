import { getGraphAccessToken } from "../auth/getGraphAccessToken";

const GRAPH_BASE_URL = "https://graph.microsoft.com/v1.0";

export async function fetchMyProfilePhoto() {
  const token = await getGraphAccessToken();

  if (!token) {
    return null;
  }

  const response = await fetch(`${GRAPH_BASE_URL}/me/photo/$value`, {
    method: "GET",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (response.status === 404) {
    return null;
  }

  if (!response.ok) {
    throw new Error(`Graph photo error: HTTP ${response.status}`);
  }

  const blob = await response.blob();
  return URL.createObjectURL(blob);
}