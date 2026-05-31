import { render, type RenderOptions } from "@testing-library/react";
import { MemoryRouter, type MemoryRouterProps } from "react-router-dom";
import { I18nextProvider } from "react-i18next";
import type { ReactElement, ReactNode } from "react";

import i18n from "../i18n/i18n";
import { AuthProvider } from "../context/AuthContext";
import type { User } from "../types";

type Options = Omit<RenderOptions, "wrapper"> & {
  route?: string;
  routerProps?: MemoryRouterProps;
  withAuth?: boolean;
};

export function renderWithProviders(ui: ReactElement, options: Options = {}) {
  const { route = "/", routerProps, withAuth = false, ...renderOptions } = options;

  function Wrapper({ children }: { children: ReactNode }) {
    const content = withAuth ? <AuthProvider>{children}</AuthProvider> : children;
    return (
      <I18nextProvider i18n={i18n}>
        <MemoryRouter initialEntries={[route]} {...routerProps}>
          {content}
        </MemoryRouter>
      </I18nextProvider>
    );
  }

  return render(ui, { wrapper: Wrapper, ...renderOptions });
}

export const sampleUser: User = {
  id: 1,
  username: "alice",
  email: "alice@example.com",
  is_admin: false,
  preferred_language: "en",
  include_in_rankings: true,
};
