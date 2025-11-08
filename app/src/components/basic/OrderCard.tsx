import { useState } from "react";
import { motion } from "framer-motion";
import {
  IconCheck,
  IconClock,
  IconShoppingCart,
  IconLoader2,
} from "@tabler/icons-react";
import { Separator } from "../ui/separator";

interface OrderCardProps {
  id: string;
  service: string;
  store: string;
  items: Array<{
    name: string;
    quantity: number;
    price: number;
  }>;
  subtotal: number;
  deliveryFee?: number;
  serviceFee?: number;
  total: number;
  estimatedDeliveryTime: string;
  status: "pending" | "preparing" | "delivering" | "delivered";
  onApprove?: () => Promise<void>;
  onStatusUpdate?: (
    newStatus: "pending" | "preparing" | "delivering" | "delivered"
  ) => void;
}

export const OrderCard = ({
  id,
  service,
  store,
  items,
  subtotal,
  deliveryFee = 0,
  serviceFee = 0,
  total,
  estimatedDeliveryTime,
  status,
  onApprove,
  onStatusUpdate,
}: OrderCardProps) => {
  const [isApproving, setIsApproving] = useState(false);

  const handleApprove = async () => {
    if (!onApprove) return;

    setIsApproving(true);
    try {
      await onApprove();
      onStatusUpdate?.("preparing");
    } catch (error) {
      console.error("Failed to approve order:", error);
      // You could add error handling UI here
    } finally {
      setIsApproving(false);
    }
  };
  const getStatusColor = () => {
    switch (status) {
      case "pending":
        return "text-status-yellow";
      case "preparing":
        return "text-status-blue";
      case "delivering":
        return "text-status-purple";
      case "delivered":
        return "text-status-green";
      default:
        return "text-muted-foreground";
    }
  };

  const getStatusLabel = () => {
    switch (status) {
      case "pending":
        return "Pending Approval";
      case "preparing":
        return "Preparing";
      case "delivering":
        return "On the Way";
      case "delivered":
        return "Delivered";
      default:
        return status;
    }
  };

  return (
    <motion.div
      initial={{ y: 5, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      className="w-full border border-border rounded-lg bg-card overflow-hidden"
    >
      {/* Header */}
      <div className="px-4 py-3 bg-secondary border-b border-border flex items-center justify-between">
        <div className="flex flex-col gap-1">
          <div className="flex items-center gap-2">
            <IconShoppingCart className="size-5 text-muted-foreground" />
            <span className="font-medium text-foreground">{store}</span>
          </div>
          <span className="text-xs text-muted-foreground ml-7">
            via {service}
          </span>
        </div>
        <div className={`text-sm font-medium ${getStatusColor()}`}>
          {getStatusLabel()}
        </div>
      </div>

      {/* Items */}
      <div className="px-4 py-3">
        <div className="space-y-2 mb-4">
          {items.map((item, index) => (
            <div
              key={index}
              className="flex items-center justify-between text-sm"
            >
              <div className="flex items-center gap-2 text-foreground">
                <span className="text-muted-foreground">{item.quantity}x</span>
                <span>{item.name}</span>
              </div>
              <span className="text-foreground font-medium">
                €{(item.price * item.quantity).toFixed(2)}
              </span>
            </div>
          ))}
        </div>

        {/* Price Breakdown */}
        <div className="pt-3 space-y-1.5">
          <Separator className="mb-3" />
          <div className="flex items-center justify-between text-sm text-muted-foreground">
            <span>Subtotal</span>
            <span>€{subtotal.toFixed(2)}</span>
          </div>
          {deliveryFee > 0 && (
            <div className="flex items-center justify-between text-sm text-muted-foreground">
              <span>Delivery Fee</span>
              <span>€{deliveryFee.toFixed(2)}</span>
            </div>
          )}
          {serviceFee > 0 && (
            <div className="flex items-center justify-between text-sm text-muted-foreground">
              <span>Service Fee</span>
              <span>€{serviceFee.toFixed(2)}</span>
            </div>
          )}
          <Separator className="mt-2" />
          <div className="flex items-center justify-between text-base font-semibold text-foreground pt-2">
            <span>Total</span>
            <span>€{total.toFixed(2)}</span>
          </div>
        </div>
      </div>

      {/* Delivery Time & Actions */}
      <div className="px-4 py-3 bg-secondary flex items-center justify-between relative">
        <Separator className="absolute top-0 left-0 right-0" />
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <IconClock className="size-4" />
          <span>Est. delivery: {estimatedDeliveryTime}</span>
        </div>
        {status === "pending" && onApprove && (
          <button
            onClick={handleApprove}
            disabled={isApproving}
            className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md text-sm font-medium hover:opacity-90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isApproving ? (
              <>
                <IconLoader2 className="size-4 animate-spin" />
                Approving...
              </>
            ) : (
              <>
                <IconCheck className="size-4" />
                Approve Order
              </>
            )}
          </button>
        )}
      </div>
    </motion.div>
  );
};
