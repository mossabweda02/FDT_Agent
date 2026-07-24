import { InteractionRequiredAuthError } from "@azure/msal-browser";
import { msalInstance } from "./msalInstance";

const graphRequest = {
  scopes: ["User.Read"],
};

export async function getGraphAccessToken() {
  const activeAccount = msalInstance.getActiveAccount();
  const accounts = msalInstance.getAllAccounts();
  const account = activeAccount || accounts[0];

  if (!account) {
    throw new Error("Aucun utilisateur connecté.");
  }

  const request = {
    ...graphRequest,
    account,
  };

  try {
    const response = await msalInstance.acquireTokenSilent(request);
    return response.accessToken;
  } catch (error) {
    if (error instanceof InteractionRequiredAuthError) {
      await msalInstance.acquireTokenRedirect(request);
      return null;
    }

    throw error;
  }
}