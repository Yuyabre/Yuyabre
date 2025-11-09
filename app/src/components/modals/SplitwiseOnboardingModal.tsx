import { useState, useEffect, useCallback } from "react";
import { toast } from "sonner";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "../ui/dialog";
import { useStore } from "@/store/useStore";
import { authApi } from "@/lib/api";
import { IconWallet, IconCheck, IconLoader2 } from "@tabler/icons-react";

interface SplitwiseOnboardingModalProps {
  open: boolean;
  onComplete: () => void;
  onSkip?: () => void;
}

export function SplitwiseOnboardingModal({
  open,
  onComplete,
  onSkip,
}: SplitwiseOnboardingModalProps) {
  const { currentUser } = useStore();
  const [isConnecting, setIsConnecting] = useState(false);
  const [isChecking, setIsChecking] = useState(false);
  const [isAuthorized, setIsAuthorized] = useState(false);
  const [popupWindow, setPopupWindow] = useState<Window | null>(null);

  async function handleCallback(oauthToken: string, oauthVerifier: string) {
    if (!currentUser) return;

    try {
      setIsConnecting(true);

      // Send callback data to /auth/splitwise endpoint
      // This will complete the OAuth flow and save tokens
      await authApi.handleSplitwiseCallback(
        currentUser.user_id,
        oauthToken,
        oauthVerifier
      );

      // Close popup if still open
      if (popupWindow && !popupWindow.closed) {
        popupWindow.close();
      }
      setPopupWindow(null);

      // Check status to confirm authorization
      await checkAuthStatus();
    } catch (error) {
      console.error("Error handling Splitwise callback:", error);
      toast.error(
        error instanceof Error
          ? error.message
          : "Failed to complete Splitwise connection."
      );
      setIsConnecting(false);
    }
  }

  // Check authorization status on mount
  useEffect(() => {
    if (open && currentUser) {
      checkAuthStatus();
    }
  }, [open, currentUser]);

  // Handle callback from URL parameters (if redirected instead of popup)
  // This happens when Splitwise redirects back to our app
  useEffect(() => {
    if (!open || !currentUser) return;

    const urlParams = new URLSearchParams(window.location.search);
    const oauthToken = urlParams.get("oauth_token");
    const oauthVerifier = urlParams.get("oauth_verifier");

    if (oauthToken && oauthVerifier) {
      // Clean URL
      window.history.replaceState({}, "", window.location.pathname);

      // Send callback data to /auth/splitwise endpoint
      handleCallback(oauthToken, oauthVerifier);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, currentUser]);

  // Poll for authorization if popup is open
  // The backend callback endpoint handles the OAuth exchange automatically
  // We poll the status to detect when authorization completes
  useEffect(() => {
    if (!popupWindow || !currentUser) return;

    const interval = setInterval(async () => {
      if (popupWindow.closed) {
        clearInterval(interval);
        setPopupWindow(null);
        setIsConnecting(false);
        // Check status after popup closes
        // The backend callback should have completed by now
        await checkAuthStatus();
      } else {
        // Poll status while popup is open to detect when callback completes
        const status = await authApi.checkSplitwiseStatus(currentUser.user_id);
        if (status.authorized) {
          clearInterval(interval);
          popupWindow.close();
          setPopupWindow(null);
          setIsConnecting(false);
          setIsAuthorized(true);
          toast.success("Splitwise connected successfully!");
          setTimeout(() => {
            onComplete();
          }, 1000);
        }
      }
    }, 2000);

    // Cleanup after 5 minutes
    const timeout = setTimeout(() => {
      clearInterval(interval);
      if (popupWindow && !popupWindow.closed) {
        popupWindow.close();
      }
      setPopupWindow(null);
      setIsConnecting(false);
    }, 5 * 60 * 1000);

    return () => {
      clearInterval(interval);
      clearTimeout(timeout);
    };
  }, [popupWindow, currentUser, onComplete]);

  async function checkAuthStatus() {
    if (!currentUser) return;

    setIsChecking(true);
    try {
      const status = await authApi.checkSplitwiseStatus(currentUser.user_id);
      setIsAuthorized(status.authorized);

      if (status.authorized && isConnecting) {
        setIsConnecting(false);
        toast.success("Splitwise connected successfully!");
        // Small delay to show success message
        setTimeout(() => {
          onComplete();
        }, 1000);
      }
    } catch (error) {
      console.error("Error checking Splitwise status:", error);
      setIsAuthorized(false);
    } finally {
      setIsChecking(false);
    }
  }

  async function handleConnect() {
    if (!currentUser) {
      toast.error("Please log in first.");
      return;
    }

    setIsConnecting(true);
    try {
      // Construct callback URL - use current window location
      const callbackUrl = `${window.location.origin}${window.location.pathname}`;

      // Get authorization URL with callback URL
      const response = await authApi.getSplitwiseAuthorizeUrl(
        currentUser.user_id,
        callbackUrl
      );

      if (response.authorize_url) {
        // Open in popup window
        const width = 600;
        const height = 700;
        const left = window.screenX + (window.outerWidth - width) / 2;
        const top = window.screenY + (window.outerHeight - height) / 2;

        const popup = window.open(
          response.authorize_url,
          "splitwise-auth",
          `width=${width},height=${height},left=${left},top=${top},scrollbars=yes,resizable=yes`
        );

        if (!popup) {
          toast.error("Please allow popups to connect Splitwise.");
          setIsConnecting(false);
          return;
        }

        setPopupWindow(popup);

        // Listen for popup to close
        const checkClosed = setInterval(() => {
          if (popup.closed) {
            clearInterval(checkClosed);
            setPopupWindow(null);
            setIsConnecting(false);
            checkAuthStatus();
          }
        }, 1000);
      }
    } catch (error) {
      console.error("Error connecting Splitwise:", error);
      toast.error(
        error instanceof Error
          ? error.message
          : "Failed to connect Splitwise. Please try again."
      );
      setIsConnecting(false);
    }
  }

  return (
    <Dialog open={open} modal={true}>
      <DialogContent
        className="max-w-md"
        onInteractOutside={(e) => e.preventDefault()}
        hideCloseButton={true}
      >
        <DialogHeader>
          <DialogTitle className="text-foreground flex items-center gap-2">
            <IconWallet className="size-5 text-primary" />
            Connect Splitwise
          </DialogTitle>
          <DialogDescription className="text-muted-foreground">
            Link your Splitwise account to automatically split expenses with
            your flatmates
          </DialogDescription>
        </DialogHeader>

        <div className="mt-4 space-y-6">
          {isChecking && !isAuthorized ? (
            <div className="flex items-center justify-center gap-2 text-sm text-muted-foreground">
              <IconLoader2 className="size-4 animate-spin" />
              Checking connection status...
            </div>
          ) : isAuthorized ? (
            <div className="space-y-4">
              <div className="flex items-center gap-3 rounded-lg border border-green-500/20 bg-green-500/10 p-4">
                <div className="flex size-10 items-center justify-center rounded-full bg-green-500/20">
                  <IconCheck className="size-5 text-green-500" />
                </div>
                <div>
                  <p className="font-medium text-foreground">
                    Splitwise Connected
                  </p>
                  <p className="text-xs text-muted-foreground">
                    Your expenses will be automatically synced
                  </p>
                </div>
              </div>
              <button
                onClick={onComplete}
                className="w-full rounded-md bg-primary px-3 py-2 text-sm font-medium text-primary-foreground transition-opacity hover:opacity-90"
              >
                Continue
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="space-y-3 text-sm text-muted-foreground">
                <p>
                  Connect your Splitwise account to enable automatic expense
                  splitting:
                </p>
                <ul className="list-disc space-y-1 pl-5">
                  <li>Orders are automatically added as Splitwise expenses</li>
                  <li>Costs are split evenly among your flatmates</li>
                  <li>No manual entry required</li>
                </ul>
              </div>

              <div className="flex flex-col gap-2">
                <button
                  onClick={handleConnect}
                  disabled={isConnecting}
                  className="flex items-center justify-center gap-2 w-full rounded-md bg-primary px-3 py-2 text-sm font-medium text-primary-foreground transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-70"
                >
                  {isConnecting ? (
                    <>
                      <IconLoader2 className="size-4 animate-spin" />
                      Connecting...
                    </>
                  ) : (
                    <>
                      <IconWallet className="size-4" />
                      Connect Splitwise
                    </>
                  )}
                </button>

                {onSkip && (
                  <button
                    onClick={onSkip}
                    disabled={isConnecting}
                    className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm font-medium text-foreground transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-70"
                  >
                    Skip for now
                  </button>
                )}
              </div>

              {isConnecting && (
                <div className="rounded-lg border border-border bg-muted/50 p-3 text-xs text-muted-foreground">
                  <p className="font-medium mb-1">
                    Authorization in progress...
                  </p>
                  <p>Please complete the authorization in the popup window.</p>
                </div>
              )}
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
