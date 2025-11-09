import { FormEvent, useState } from "react";
import { toast } from "sonner";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "../ui/dialog";
import { useStore } from "@/store/useStore";
import {
  useCreateHousehold,
  useJoinHousehold,
  useGetUser,
} from "@/lib/queries";
import { authApi } from "@/lib/api";
import { authStorage } from "@/lib/authStorage";
import { IconPlus, IconUserPlus } from "@tabler/icons-react";

interface HouseholdOnboardingModalProps {
  open: boolean;
}

type OnboardingMode = "choose" | "create" | "join";

export function HouseholdOnboardingModal({
  open,
}: HouseholdOnboardingModalProps) {
  const { currentUser, setCurrentUser, setCurrentHousehold } = useStore();
  const createHousehold = useCreateHousehold();
  const joinHousehold = useJoinHousehold();
  const { refetch: refetchUser } = useGetUser(currentUser?.user_id ?? null);

  const [mode, setMode] = useState<OnboardingMode>("choose");
  const [householdName, setHouseholdName] = useState("");
  const [address, setAddress] = useState("");
  const [city, setCity] = useState("");
  const [postalCode, setPostalCode] = useState("");
  const [country, setCountry] = useState("");
  const [whatsappGroupId, setWhatsappGroupId] = useState("");
  const [whatsappGroupName, setWhatsappGroupName] = useState("");
  const [notes, setNotes] = useState("");
  const [inviteCode, setInviteCode] = useState("");

  const isBusy = createHousehold.isPending || joinHousehold.isPending;

  const handleCreateHousehold = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!currentUser) {
      toast.error("Please log in first.");
      return;
    }

    if (!householdName.trim()) {
      toast.error("Household name is required.");
      return;
    }

    createHousehold.mutate(
      {
        userId: currentUser.user_id,
        data: {
          name: householdName.trim(),
          address: address.trim() || null,
          city: city.trim() || null,
          postal_code: postalCode.trim() || null,
          country: country.trim() || null,
          whatsapp_group_id: whatsappGroupId.trim() || null,
          whatsapp_group_name: whatsappGroupName.trim() || null,
          notes: notes.trim() || null,
        },
      },
      {
        onSuccess: async (household) => {
          setCurrentHousehold(household);
          authStorage.saveHousehold(household);
          // Refetch user to get updated household_id
          const { data: updatedUser } = await refetchUser();
          if (updatedUser) {
            setCurrentUser(updatedUser);
            authStorage.saveUser(updatedUser);
          }
          toast.success(`Household "${household.name}" created!`);
          setMode("choose");
          setHouseholdName("");
          setAddress("");
          setCity("");
          setPostalCode("");
          setCountry("");
          setWhatsappGroupId("");
          setWhatsappGroupName("");
          setNotes("");
        },
        onError: (error) => {
          toast.error(error.message);
        },
      }
    );
  };

  const handleJoinHousehold = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!currentUser) {
      toast.error("Please log in first.");
      return;
    }

    if (!inviteCode.trim()) {
      toast.error("Invite code is required.");
      return;
    }

    joinHousehold.mutate(
      {
        userId: currentUser.user_id,
        data: {
          invite_code: inviteCode.trim(),
        },
      },
      {
        onSuccess: async () => {
          toast.success("Successfully joined household!");
          // Refetch user to get updated household_id
          const { data: updatedUser } = await refetchUser();
          if (updatedUser && updatedUser.household_id) {
            setCurrentUser(updatedUser);
            authStorage.saveUser(updatedUser);
            // Fetch household details
            try {
              const household = await authApi.getHousehold(updatedUser.household_id);
              setCurrentHousehold(household);
              authStorage.saveHousehold(household);
            } catch (error) {
              console.error("Failed to fetch household:", error);
              // User will be updated, App.tsx will fetch household automatically
            }
          }
          setMode("choose");
          setInviteCode("");
        },
        onError: (error) => {
          toast.error(error.message);
        },
      }
    );
  };

  const renderChooseMode = () => (
    <div className="space-y-6">
      <div className="text-center">
        <h3 className="text-lg font-semibold text-foreground mb-2">
          Set up your household
        </h3>
        <p className="text-sm text-muted-foreground">
          Create a new household or join an existing one with an invite code.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <button
          type="button"
          onClick={() => setMode("create")}
          className="flex flex-col items-center gap-3 rounded-lg border-2 border-border bg-card p-6 transition-all hover:border-primary hover:bg-muted/50"
        >
          <div className="rounded-full bg-primary/10 p-3">
            <IconPlus className="size-6 text-primary" />
          </div>
          <div className="text-center">
            <h4 className="font-semibold text-foreground">Create New</h4>
            <p className="text-xs text-muted-foreground mt-1">
              Start a new household
            </p>
          </div>
        </button>

        <button
          type="button"
          onClick={() => setMode("join")}
          className="flex flex-col items-center gap-3 rounded-lg border-2 border-border bg-card p-6 transition-all hover:border-primary hover:bg-muted/50"
        >
          <div className="rounded-full bg-primary/10 p-3">
            <IconUserPlus className="size-6 text-primary" />
          </div>
          <div className="text-center">
            <h4 className="font-semibold text-foreground">Join Existing</h4>
            <p className="text-xs text-muted-foreground mt-1">
              Use an invite code
            </p>
          </div>
        </button>
      </div>
    </div>
  );

  const renderCreateMode = () => (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={() => {
            setMode("choose");
            setHouseholdName("");
            setAddress("");
            setCity("");
            setPostalCode("");
            setCountry("");
            setWhatsappGroupId("");
            setWhatsappGroupName("");
            setNotes("");
          }}
          className="text-sm text-muted-foreground hover:text-foreground"
        >
          ← Back
        </button>
      </div>

      <form onSubmit={handleCreateHousehold} className="space-y-4">
        <div className="space-y-6">
          <div className="space-y-1.5">
            <label className="text-sm font-medium text-foreground">
              Household name *
            </label>
            <input
              type="text"
              className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
              value={householdName}
              onChange={(event) => setHouseholdName(event.target.value)}
              placeholder="E.g. Main Street Flat"
              disabled={isBusy}
              required
              autoFocus
            />
          </div>

          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <div className="space-y-1.5 sm:col-span-2">
              <label className="text-sm font-medium text-muted-foreground">
                Address
              </label>
              <input
                type="text"
                className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                value={address}
                onChange={(event) => setAddress(event.target.value)}
                placeholder="Street and number"
                disabled={isBusy}
              />
            </div>
            <div className="space-y-1.5">
              <label className="text-sm font-medium text-muted-foreground">
                City
              </label>
              <input
                type="text"
                className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                value={city}
                onChange={(event) => setCity(event.target.value)}
                placeholder="City"
                disabled={isBusy}
              />
            </div>
            <div className="space-y-1.5">
              <label className="text-sm font-medium text-muted-foreground">
                Postal code
              </label>
              <input
                type="text"
                className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                value={postalCode}
                onChange={(event) => setPostalCode(event.target.value)}
                placeholder="Postal code"
                disabled={isBusy}
              />
            </div>
            <div className="space-y-1.5 sm:col-span-2">
              <label className="text-sm font-medium text-muted-foreground">
                Country
              </label>
              <input
                type="text"
                className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                value={country}
                onChange={(event) => setCountry(event.target.value)}
                placeholder="Country"
                disabled={isBusy}
              />
            </div>
          </div>

          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <div className="space-y-1.5">
              <label className="text-sm font-medium text-muted-foreground">
                WhatsApp group ID
              </label>
              <input
                type="text"
                className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                value={whatsappGroupId}
                onChange={(event) => setWhatsappGroupId(event.target.value)}
                placeholder="Optional"
                disabled={isBusy}
              />
            </div>
            <div className="space-y-1.5">
              <label className="text-sm font-medium text-muted-foreground">
                WhatsApp group name
              </label>
              <input
                type="text"
                className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                value={whatsappGroupName}
                onChange={(event) => setWhatsappGroupName(event.target.value)}
                placeholder="Optional"
                disabled={isBusy}
              />
            </div>
          </div>

          <div className="space-y-1.5">
            <label className="text-sm font-medium text-muted-foreground">
              Notes for your flatmates
            </label>
            <textarea
              className="h-20 w-full rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
              value={notes}
              onChange={(event) => setNotes(event.target.value)}
              placeholder="Share any details about shared expenses, door codes, or delivery preferences"
              disabled={isBusy}
            />
          </div>
        </div>

        <button
          type="submit"
          className="w-full rounded-md bg-primary px-3 py-2 text-sm font-medium text-primary-foreground transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-70"
          disabled={isBusy}
        >
          {createHousehold.isPending
            ? "Creating household..."
            : "Create household"}
        </button>
      </form>
    </div>
  );

  const renderJoinMode = () => (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={() => {
            setMode("choose");
            setInviteCode("");
          }}
          className="text-sm text-muted-foreground hover:text-foreground"
        >
          ← Back
        </button>
      </div>

      <form onSubmit={handleJoinHousehold} className="space-y-4">
        <div className="space-y-1.5">
          <label className="text-sm font-medium text-foreground">
            Invite Code *
          </label>
          <input
            type="text"
            className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
            value={inviteCode}
            onChange={(event) => setInviteCode(event.target.value)}
            placeholder="Enter the invite code"
            disabled={isBusy}
            required
            autoFocus
          />
          <p className="text-xs text-muted-foreground">
            Ask your flatmate for the household invite code.
          </p>
        </div>

        <button
          type="submit"
          className="w-full rounded-md bg-primary px-3 py-2 text-sm font-medium text-primary-foreground transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-70"
          disabled={isBusy}
        >
          {joinHousehold.isPending ? "Joining..." : "Join household"}
        </button>
      </form>
    </div>
  );

  return (
    <Dialog open={open} modal={true}>
      <DialogContent className="max-w-md" onInteractOutside={(e) => e.preventDefault()}>
        <DialogHeader>
          <DialogTitle className="text-foreground">
            {mode === "choose"
              ? "Welcome to Yuyabre"
              : mode === "create"
              ? "Create Household"
              : "Join Household"}
          </DialogTitle>
          <DialogDescription className="text-muted-foreground">
            {mode === "choose"
              ? "Get started by setting up your household"
              : mode === "create"
              ? "Create a new household for you and your flatmates"
              : "Join an existing household with an invite code"}
          </DialogDescription>
        </DialogHeader>
        <div className="mt-4">
          {mode === "choose" && renderChooseMode()}
          {mode === "create" && renderCreateMode()}
          {mode === "join" && renderJoinMode()}
        </div>
      </DialogContent>
    </Dialog>
  );
}

