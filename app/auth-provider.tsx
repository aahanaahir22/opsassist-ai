"use client";

import { Auth0Provider, useAuth0 } from "@auth0/auth0-react";
import { createContext, useCallback, useContext, type ReactNode } from "react";

type OpsAuth = {
  configured: boolean;
  authenticated: boolean;
  loading: boolean;
  name: string;
  login: () => Promise<void>;
  logout: () => Promise<void>;
  getAccessToken: () => Promise<string | null>;
};

const guest: OpsAuth = {
  configured: false,
  authenticated: false,
  loading: false,
  name: "Portfolio guest",
  login: async () => undefined,
  logout: async () => undefined,
  getAccessToken: async () => null,
};
const OpsAuthContext = createContext<OpsAuth>(guest);

function AuthBridge({ children }: { children: ReactNode }) {
  const auth = useAuth0();
  const { getAccessTokenSilently, isAuthenticated } = auth;
  const audience = process.env.NEXT_PUBLIC_AUTH0_AUDIENCE as string;
  const getAccessToken = useCallback(async () => {
    if (!isAuthenticated) return null;
    return getAccessTokenSilently({ authorizationParams: { audience } });
  }, [isAuthenticated, getAccessTokenSilently, audience]);
  const value: OpsAuth = {
    configured: true,
    authenticated: auth.isAuthenticated,
    loading: auth.isLoading,
    name: auth.user?.name || auth.user?.email || "Authenticated operator",
    login: async () =>
      auth.loginWithRedirect({ authorizationParams: { audience } }),
    logout: async () =>
      auth.logout({ logoutParams: { returnTo: window.location.origin } }),
    getAccessToken,
  };
  return (
    <OpsAuthContext.Provider value={value}>{children}</OpsAuthContext.Provider>
  );
}

export function OpsAssistAuthProvider({ children }: { children: ReactNode }) {
  const domain = process.env.NEXT_PUBLIC_AUTH0_DOMAIN;
  const clientId = process.env.NEXT_PUBLIC_AUTH0_CLIENT_ID;
  const audience = process.env.NEXT_PUBLIC_AUTH0_AUDIENCE;
  if (!domain || !clientId || !audience)
    return (
      <OpsAuthContext.Provider value={guest}>
        {children}
      </OpsAuthContext.Provider>
    );
  return (
    <Auth0Provider
      domain={domain}
      clientId={clientId}
      authorizationParams={{
        redirect_uri:
          typeof window === "undefined" ? undefined : window.location.origin,
        audience,
      }}
      cacheLocation="memory"
      useRefreshTokens={false}
    >
      <AuthBridge>{children}</AuthBridge>
    </Auth0Provider>
  );
}

export function useOpsAssistAuth() {
  return useContext(OpsAuthContext);
}
