import { useState, useEffect } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "../ui/dialog";
import { Separator } from "../ui/separator";
import { useTheme } from "../basic/ThemeProvider";
import { useStore } from "@/store/useStore";
import { authApi } from "@/lib/api";
import {
  IconPalette,
  IconWallet,
  IconCheck,
  IconLoader2,
  IconMoon,
  IconSun,
  IconDeviceDesktop,
} from "@tabler/icons-react";

interface SettingsModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

type Theme = "light" | "dark" | "system";

export function SettingsModal({ open, onOpenChange }: SettingsModalProps) {
  const { theme, setTheme } = useTheme();
  const { currentUser } = useStore();
  const [isCheckingSplitwise, setIsCheckingSplitwise] = useState(false);
  const [isSplitwiseConnected, setIsSplitwiseConnected] = useState(false);

  // Check Splitwise status when modal opens
  useEffect(() => {
    if (open && currentUser) {
      checkSplitwiseStatus();
    }
  }, [open, currentUser]);

  async function checkSplitwiseStatus() {
    if (!currentUser) return;

    setIsCheckingSplitwise(true);
    try {
      const status = await authApi.checkSplitwiseStatus(currentUser.user_id);
      setIsSplitwiseConnected(status.authorized);
    } catch (error) {
      console.error("Error checking Splitwise status:", error);
      setIsSplitwiseConnected(false);
    } finally {
      setIsCheckingSplitwise(false);
    }
  }

  const handleThemeChange = (newTheme: Theme) => {
    setTheme(newTheme);
  };

  const themeOptions: { value: Theme; label: string; icon: React.ReactNode }[] = [
    {
      value: "light",
      label: "Light",
      icon: <IconSun className="size-4" />,
    },
    {
      value: "dark",
      label: "Dark",
      icon: <IconMoon className="size-4" />,
    },
    {
      value: "system",
      label: "System",
      icon: <IconDeviceDesktop className="size-4" />,
    },
  ];

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle className="text-foreground flex items-center gap-2">
            <IconPalette className="size-5 text-primary" />
            Settings
          </DialogTitle>
          <DialogDescription className="text-muted-foreground">
            Manage your app preferences and account settings
          </DialogDescription>
        </DialogHeader>

        <div className="mt-4 space-y-6">
          {/* Theme Selection */}
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <IconPalette className="size-4 text-muted-foreground" />
              <h3 className="text-sm font-semibold text-foreground">Appearance</h3>
            </div>
            <div className="grid grid-cols-3 gap-2">
              {themeOptions.map((option) => {
                const isSelected = theme === option.value;
                return (
                  <button
                    key={option.value}
                    onClick={() => handleThemeChange(option.value)}
                    className={`flex flex-col items-center gap-2 rounded-lg border-2 p-3 transition-all ${
                      isSelected
                        ? "border-primary bg-primary/10"
                        : "border-border bg-card hover:border-primary/50 hover:bg-muted/50"
                    }`}
                  >
                    <div className="text-foreground">{option.icon}</div>
                    <span
                      className={`text-xs font-medium ${
                        isSelected ? "text-primary" : "text-muted-foreground"
                      }`}
                    >
                      {option.label}
                    </span>
                    {isSelected && (
                      <IconCheck className="size-3.5 text-primary" />
                    )}
                  </button>
                );
              })}
            </div>
          </div>

          <Separator />

          {/* Splitwise Connection Status */}
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <IconWallet className="size-4 text-muted-foreground" />
              <h3 className="text-sm font-semibold text-foreground">
                Integrations
              </h3>
            </div>
            <div className="rounded-lg border border-border bg-card p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="flex size-10 items-center justify-center rounded-full bg-primary/10">
                    <IconWallet className="size-5 text-primary" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-foreground">
                      Splitwise
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {isCheckingSplitwise
                        ? "Checking status..."
                        : isSplitwiseConnected
                        ? "Connected"
                        : "Not connected"}
                    </p>
                  </div>
                </div>
                {isCheckingSplitwise ? (
                  <IconLoader2 className="size-4 animate-spin text-muted-foreground" />
                ) : isSplitwiseConnected ? (
                  <div className="flex items-center gap-1 rounded-full bg-green-500/10 px-2 py-1">
                    <IconCheck className="size-3 text-green-500" />
                    <span className="text-xs font-medium text-green-500">
                      Active
                    </span>
                  </div>
                ) : (
                  <span className="text-xs text-muted-foreground">
                    Not connected
                  </span>
                )}
              </div>
            </div>
          </div>

          <Separator />

          {/* Account Info */}
          {currentUser && (
            <div className="space-y-3">
              <h3 className="text-sm font-semibold text-foreground">Account</h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Name</span>
                  <span className="font-medium text-foreground">
                    {currentUser.name}
                  </span>
                </div>
                {currentUser.email && (
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Email</span>
                    <span className="font-medium text-foreground">
                      {currentUser.email}
                    </span>
                  </div>
                )}
                {currentUser.phone && (
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Phone</span>
                    <span className="font-medium text-foreground">
                      {currentUser.phone}
                    </span>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}

