import { useState } from "react";
import { Modal } from "../basic/Modal";
import { Avatar, AvatarImage, AvatarFallback } from "../ui/avatar";
import { Separator } from "../ui/separator";
import { Label } from "../ui/label";
import { useStore } from "../../store/useStore";
import { userApi } from "../../lib/api";
import { IconUsers, IconPlus } from "@tabler/icons-react";

interface GroupModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function GroupModal({ open, onOpenChange }: GroupModalProps) {
  const { currentUser, currentGroup, setCurrentGroup } = useStore();
  const [showAddFlatmate, setShowAddFlatmate] = useState(false);
  const [flatmateEmail, setFlatmateEmail] = useState("");

  const handleAddFlatmate = async () => {
    if (!flatmateEmail.trim() || !currentUser?.isAdmin) return;

    try {
      const updatedGroup = await userApi.addFlatmate(flatmateEmail);
      setCurrentGroup(updatedGroup);
      setFlatmateEmail("");
      setShowAddFlatmate(false);
    } catch (error) {
      console.error("Failed to add flatmate:", error);
    }
  };

  const getInitials = (name: string) => {
    return name
      .split(" ")
      .map((n) => n[0])
      .join("")
      .toUpperCase()
      .slice(0, 2);
  };

  if (!currentGroup) return null;

  return (
    <Modal
      open={open}
      onOpenChange={onOpenChange}
      title={currentGroup.name}
      description="Manage your flat and flatmates"
    >
      <div className="space-y-4">
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <IconUsers className="size-4" />
          <span>{currentGroup.members.length} flatmate{currentGroup.members.length !== 1 ? "s" : ""}</span>
        </div>

        <div className="space-y-2">
          {currentGroup.members.map((member) => (
            <div
              key={member.id}
              className={`flex items-center gap-3 p-3 rounded-lg border ${
                member.id === currentUser?.id
                  ? "bg-muted border-border"
                  : "border-border"
              }`}
            >
              <Avatar>
                <AvatarImage src={member.avatar} alt={member.name} />
                <AvatarFallback>{getInitials(member.name)}</AvatarFallback>
              </Avatar>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="font-medium text-foreground">
                    {member.name}
                  </span>
                  {member.id === currentUser?.id && (
                    <span className="text-xs text-muted-foreground">(You)</span>
                  )}
                  {member.isAdmin && (
                    <span className="text-xs px-2 py-0.5 bg-muted text-muted-foreground rounded">
                      Admin
                    </span>
                  )}
                </div>
                <div className="text-sm text-muted-foreground">{member.email}</div>
              </div>
            </div>
          ))}
        </div>

        {currentUser?.isAdmin && (
          <div className="pt-2">
            <Separator className="mb-4" />
            {showAddFlatmate ? (
              <div className="space-y-2">
                <Label htmlFor="flatmate-email" className="sr-only">
                  Email address
                </Label>
                <input
                  id="flatmate-email"
                  type="email"
                  placeholder="Email address"
                  value={flatmateEmail}
                  onChange={(e) => setFlatmateEmail(e.target.value)}
                  className="w-full px-3 py-2 border border-border rounded-md bg-background text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      handleAddFlatmate();
                    } else if (e.key === "Escape") {
                      setShowAddFlatmate(false);
                      setFlatmateEmail("");
                    }
                  }}
                  autoFocus
                />
                <div className="flex gap-2">
                  <button
                    onClick={handleAddFlatmate}
                    className="flex-1 px-3 py-2 bg-primary text-primary-foreground rounded-md text-sm font-medium hover:opacity-90 transition-colors"
                  >
                    Add
                  </button>
                  <button
                    onClick={() => {
                      setShowAddFlatmate(false);
                      setFlatmateEmail("");
                    }}
                    className="flex-1 px-3 py-2 border border-border rounded-md text-sm hover:bg-muted transition-colors"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            ) : (
              <button
                onClick={() => setShowAddFlatmate(true)}
                className="w-full flex items-center justify-center gap-2 px-3 py-2 border border-dashed border-border rounded-md text-sm text-muted-foreground hover:border-border hover:text-foreground transition-colors"
              >
                <IconPlus className="size-4" />
                <span>Add Flatmate</span>
              </button>
            )}
          </div>
        )}
      </div>
    </Modal>
  );
}

