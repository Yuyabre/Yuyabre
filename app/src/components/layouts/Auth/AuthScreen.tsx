import { type FormEvent, useMemo, useState } from "react";
import { toast } from "sonner";
import { useLogin, useSignup } from "@/lib/queries";
import { useStore } from "@/store/useStore";
import { authStorage } from "@/lib/authStorage";
import type { SignupRequest, UserPreferenceRequest } from "@/types/users";
import {
  IconCircleCheck,
  IconUsersGroup,
  IconReceipt2,
  IconSparkles,
} from "@tabler/icons-react";

type AuthMode = "login" | "signup";

const defaultPreferences: UserPreferenceRequest = {
  dietary_restrictions: [],
  allergies: [],
  favorite_brands: [],
  disliked_items: [],
};

const parseList = (value: string): string[] =>
  value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);

export function AuthScreen() {
  const [mode, setMode] = useState<AuthMode>("login");
  const [signupForm, setSignupForm] = useState<SignupRequest>({
    name: "",
    email: "",
    password: "",
    phone: "",
    discord_user_id: "",
    preferences: { ...defaultPreferences },
  });
  const [loginForm, setLoginForm] = useState({ email: "", password: "" });

  const { setCurrentUser, setCurrentHousehold } = useStore();
  const loginMutation = useLogin();
  const signupMutation = useSignup();

  const isLoading = useMemo(
    () => loginMutation.isPending || signupMutation.isPending,
    [loginMutation.isPending, signupMutation.isPending]
  );

  const handleLoginSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!loginForm.email || !loginForm.password) {
      toast.error("Please enter your email and password.");
      return;
    }

    loginMutation.mutate(
      { email: loginForm.email, password: loginForm.password },
      {
        onSuccess: (user) => {
          setCurrentUser(user);
          setCurrentHousehold(null);
          authStorage.saveUser(user);
          authStorage.saveHousehold(null);
          toast.success(`Welcome back, ${user.name}!`);
        },
        onError: (error) => {
          toast.error(error.message);
        },
      }
    );
  };

  const handleSignupSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (!signupForm.name || !signupForm.password) {
      toast.error("Name and password are required.");
      return;
    }

    const preferences: UserPreferenceRequest | null = signupForm.preferences
      ? {
          dietary_restrictions:
            signupForm.preferences.dietary_restrictions ?? [],
          allergies: signupForm.preferences.allergies ?? [],
          favorite_brands: signupForm.preferences.favorite_brands ?? [],
          disliked_items: signupForm.preferences.disliked_items ?? [],
        }
      : null;

    const payload: SignupRequest = {
      name: signupForm.name,
      password: signupForm.password,
      email: signupForm.email || null,
      phone: signupForm.phone || null,
      discord_user_id: signupForm.discord_user_id || null,
      preferences,
    };

    signupMutation.mutate(payload, {
      onSuccess: (user) => {
        setCurrentUser(user);
        setCurrentHousehold(null);
        authStorage.saveUser(user);
        authStorage.saveHousehold(null);
        toast.success("Account created! Let's set up your household.");
      },
      onError: (error) => {
        toast.error(error.message);
      },
    });
  };

  const inputClasses =
    "w-full rounded-xl border border-border/60 bg-background/60 px-4 py-3 text-sm text-foreground shadow-sm transition focus:border-primary/50 focus:outline-none focus:ring-2 focus:ring-primary/30";

  const fieldsetClasses =
    "space-y-5 rounded-2xl border border-border/60 bg-muted/10 p-5";

  const legendClasses =
    "text-xs font-semibold uppercase tracking-[0.2em] text-muted-foreground";

  const renderLogin = () => (
    <form className="flex flex-col gap-6" onSubmit={handleLoginSubmit}>
      <div className="space-y-1.5">
        <label className="text-sm font-medium text-foreground">Email</label>
        <input
          type="email"
          className={inputClasses}
          placeholder="you@example.com"
          value={loginForm.email}
          onChange={(event) =>
            setLoginForm((prev) => ({ ...prev, email: event.target.value }))
          }
          required
          autoComplete="email"
        />
      </div>
      <div className="space-y-1.5">
        <div className="flex items-center justify-between">
          <label className="text-sm font-medium text-foreground">
            Password
          </label>
          <span className="text-xs text-muted-foreground">
            Minimum 8 characters
          </span>
        </div>
        <input
          type="password"
          className={inputClasses}
          placeholder="••••••••"
          value={loginForm.password}
          onChange={(event) =>
            setLoginForm((prev) => ({ ...prev, password: event.target.value }))
          }
          required
          autoComplete="current-password"
        />
      </div>
      <div className="mt-2 flex flex-col gap-3">
        <button
          type="submit"
          className="w-full rounded-xl bg-primary px-4 py-3 text-sm font-medium text-primary-foreground transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-70"
          disabled={isLoading}
        >
          {isLoading ? "Logging in..." : "Log in"}
        </button>
        <p className="text-center text-xs text-muted-foreground">
          Trouble logging in? Ask the household admin to confirm your invite.
        </p>
      </div>
    </form>
  );

  const renderSignup = () => (
    <form className="flex flex-col gap-6" onSubmit={handleSignupSubmit}>
      <fieldset className={fieldsetClasses}>
        <legend className={legendClasses}>Profile</legend>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div className="space-y-1.5 sm:col-span-2">
            <label className="text-sm font-medium text-foreground">
              Full name <span className="text-destructive">*</span>
            </label>
            <input
              type="text"
              className={inputClasses}
              placeholder="Alex Johnson"
              value={signupForm.name}
              onChange={(event) =>
                setSignupForm((prev) => ({ ...prev, name: event.target.value }))
              }
              required
              autoComplete="name"
            />
          </div>
          <div className="space-y-1.5">
            <label className="text-sm font-medium text-foreground">
              Email <span className="text-destructive">*</span>
            </label>
            <input
              type="email"
              className={inputClasses}
              placeholder="alex@email.com"
              value={signupForm.email ?? ""}
              onChange={(event) =>
                setSignupForm((prev) => ({
                  ...prev,
                  email: event.target.value,
                }))
              }
              autoComplete="email"
            />
          </div>
          <div className="space-y-1.5">
            <label className="text-sm font-medium text-foreground">
              Password <span className="text-destructive">*</span>
            </label>
            <input
              type="password"
              className={inputClasses}
              placeholder="Create a strong password"
              value={signupForm.password}
              onChange={(event) =>
                setSignupForm((prev) => ({
                  ...prev,
                  password: event.target.value,
                }))
              }
              required
              autoComplete="new-password"
            />
          </div>
        </div>
      </fieldset>

      <fieldset className={fieldsetClasses}>
        <legend className={legendClasses}>Contact</legend>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div className="space-y-1.5">
            <label className="text-sm font-medium text-foreground">Phone</label>
            <input
              type="tel"
              className={inputClasses}
              placeholder="+31 6 1234 5678"
              value={signupForm.phone ?? ""}
              onChange={(event) =>
                setSignupForm((prev) => ({
                  ...prev,
                  phone: event.target.value,
                }))
              }
              autoComplete="tel"
            />
          </div>
          <div className="space-y-1.5">
            <label className="text-sm font-medium text-foreground">
              Discord ID
            </label>
            <input
              type="text"
              className={inputClasses}
              placeholder="Optional - e.g., 100894387834673284648327"
              value={signupForm.discord_user_id ?? ""}
              onChange={(event) =>
                setSignupForm((prev) => ({
                  ...prev,
                  discord_user_id: event.target.value,
                }))
              }
            />
          </div>
        </div>
      </fieldset>

      <fieldset className={fieldsetClasses}>
        <legend className={legendClasses}>Household Preferences</legend>
        <p className="text-sm text-muted-foreground">
          Help your flatmates understand your tastes. Add multiple values
          separated by commas.
        </p>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div className="space-y-1.5">
            <label className="text-sm font-medium text-foreground">
              Dietary restrictions
            </label>
            <input
              type="text"
              className={inputClasses}
              placeholder="Vegetarian, Halal"
              value={
                signupForm.preferences?.dietary_restrictions?.join(", ") ?? ""
              }
              onChange={(event) =>
                setSignupForm((prev) => ({
                  ...prev,
                  preferences: {
                    ...prev.preferences,
                    dietary_restrictions: parseList(event.target.value),
                  },
                }))
              }
            />
          </div>
          <div className="space-y-1.5">
            <label className="text-sm font-medium text-foreground">
              Allergies
            </label>
            <input
              type="text"
              className={inputClasses}
              placeholder="Peanuts, Shellfish"
              value={signupForm.preferences?.allergies?.join(", ") ?? ""}
              onChange={(event) =>
                setSignupForm((prev) => ({
                  ...prev,
                  preferences: {
                    ...prev.preferences,
                    allergies: parseList(event.target.value),
                  },
                }))
              }
            />
          </div>
          <div className="space-y-1.5">
            <label className="text-sm font-medium text-foreground">
              Favourite brands
            </label>
            <input
              type="text"
              className={inputClasses}
              placeholder="Oatly, Ben & Jerry's"
              value={signupForm.preferences?.favorite_brands?.join(", ") ?? ""}
              onChange={(event) =>
                setSignupForm((prev) => ({
                  ...prev,
                  preferences: {
                    ...prev.preferences,
                    favorite_brands: parseList(event.target.value),
                  },
                }))
              }
            />
          </div>
          <div className="space-y-1.5 sm:col-span-2">
            <label className="text-sm font-medium text-foreground">
              Items you'd rather skip
            </label>
            <input
              type="text"
              className={inputClasses}
              placeholder="Brussels sprouts, Instant coffee"
              value={signupForm.preferences?.disliked_items?.join(", ") ?? ""}
              onChange={(event) =>
                setSignupForm((prev) => ({
                  ...prev,
                  preferences: {
                    ...prev.preferences,
                    disliked_items: parseList(event.target.value),
                  },
                }))
              }
            />
          </div>
        </div>
      </fieldset>

      <div className="mt-2 flex flex-col gap-3">
        <button
          type="submit"
          className="w-full rounded-xl bg-primary px-4 py-3 text-sm font-medium text-primary-foreground transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-70"
          disabled={isLoading}
        >
          {isLoading ? "Creating account..." : "Create account"}
        </button>
        <p className="text-center text-xs text-muted-foreground">
          By continuing, you agree to coordinate groceries with your flatmates
          and to share household updates through Yuyabre.
        </p>
      </div>
    </form>
  );

  return (
    <div className="relative min-h-screen overflow-hidden bg-background">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top,_rgba(99,102,241,0.15),_transparent_55%),_radial-gradient(circle_at_bottom,_rgba(16,185,129,0.12),_transparent_55%)]" />
      <div className="relative z-10 flex min-h-screen items-center justify-center px-4 py-12">
        <div className="grid w-full max-w-6xl gap-6 lg:grid-cols-[minmax(0,1.05fr)_minmax(0,1fr)]">
          <div className="relative overflow-hidden rounded-3xl border border-border/50 bg-card/70 p-8 shadow-2xl backdrop-blur md:p-12">
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_20%_20%,rgba(16,185,129,0.12),transparent_55%),radial-gradient(circle_at_80%_30%,rgba(59,130,246,0.12),transparent_55%)] opacity-80" />
            <div className="relative z-10 flex h-full flex-col gap-12">
              <div className="space-y-4">
                <span className="inline-flex items-center gap-2 rounded-full bg-primary/10 px-3 py-1 text-xs font-medium text-primary">
                  <IconSparkles className="size-3.5" />
                  Smarter shared living
                </span>
                <h1 className="text-3xl font-semibold leading-tight text-foreground md:text-4xl">
                  Coordinate groceries, expenses, and errands with your flat in
                  one place.
                </h1>
                <p className="text-sm text-muted-foreground md:text-base">
                  Yuyabre keeps kitchens stocked, budgets balanced, and
                  flatmates in sync. Join the households using automation and AI
                  to make shared living effortless.
                </p>
              </div>

              <div className="grid gap-4 sm:grid-cols-2">
                <div className="rounded-2xl border border-border/60 bg-background/70 p-4 shadow-inner">
                  <div className="flex items-center gap-3">
                    <div className="flex flex-shrink-0 size-10 items-center justify-center rounded-full bg-primary/10 text-primary">
                      <IconUsersGroup className="size-5" />
                    </div>
                    <div>
                      <p className="text-sm font-semibold text-foreground">
                        Shared household hub
                      </p>
                      <p className="text-xs text-muted-foreground">
                        One place for inventory, chores, orders, and finances.
                      </p>
                    </div>
                  </div>
                </div>
                <div className="rounded-2xl border border-border/60 bg-background/70 p-4 shadow-inner">
                  <div className="flex items-center gap-3">
                    <div className="flex flex-shrink-0 size-10 items-center justify-center rounded-full bg-emerald-500/10 text-emerald-500">
                      <IconReceipt2 className="size-5" />
                    </div>
                    <div>
                      <p className="text-sm font-semibold text-foreground">
                        Automated expense sync
                      </p>
                      <p className="text-xs text-muted-foreground">
                        Track orders and Splitwise balances automatically.
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              <ul className="space-y-3 text-sm text-foreground">
                {[
                  "AI suggestions keep staples stocked without over-ordering.",
                  "Voice and chat commands to create, update, or check inventory.",
                  "Invite flatmates instantly with household codes & Discord sync.",
                ].map((item) => (
                  <li key={item} className="flex items-start gap-3">
                    <span className="mt-1 flex h-5 w-5 items-center justify-center rounded-full bg-primary/10 text-primary">
                      <IconCircleCheck className="size-3.5" />
                    </span>
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          <div className="flex flex-col rounded-3xl border border-border/60 bg-background/95 shadow-2xl backdrop-blur">
            <div className="flex items-center justify-between gap-4 border-b border-border/60 px-6 py-6">
              <div>
                <p className="text-xs uppercase tracking-[0.3em] text-muted-foreground">
                  {mode === "login" ? "Welcome back" : "Get started"}
                </p>
                <h2 className="mt-2 text-2xl font-semibold text-foreground">
                  {mode === "login"
                    ? "Sign in to your household"
                    : "Create your Yuyabre account"}
                </h2>
              </div>
              <div className="inline-flex rounded-full bg-muted/60 p-1">
                <button
                  type="button"
                  onClick={() => setMode("login")}
                  className={`rounded-full px-3 py-1 text-xs font-medium transition ${
                    mode === "login"
                      ? "bg-primary text-primary-foreground shadow"
                      : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  Log in
                </button>
                <button
                  type="button"
                  onClick={() => setMode("signup")}
                  className={`rounded-full px-3 py-1 text-xs font-medium transition ${
                    mode === "signup"
                      ? "bg-primary text-primary-foreground shadow"
                      : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  Sign up
                </button>
              </div>
            </div>

            <div className="flex-1 overflow-y-auto px-6 py-6 sm:px-8 sm:py-8">
              {mode === "login" ? renderLogin() : renderSignup()}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
