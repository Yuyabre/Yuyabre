import { useState } from "react";
import { motion } from "framer-motion";
import { IconCheck, IconClock, IconShoppingCart, IconLoader2 } from "@tabler/icons-react";

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
  onStatusUpdate?: (newStatus: "pending" | "preparing" | "delivering" | "delivered") => void;
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
        return "text-yellow-600 dark:text-yellow-400";
      case "preparing":
        return "text-blue-600 dark:text-blue-400";
      case "delivering":
        return "text-purple-600 dark:text-purple-400";
      case "delivered":
        return "text-green-600 dark:text-green-400";
      default:
        return "text-zinc-600 dark:text-zinc-400";
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
      className="w-full border border-zinc-200 dark:border-zinc-800 rounded-lg bg-white dark:bg-zinc-900 overflow-hidden"
    >
      {/* Header */}
      <div className="px-4 py-3 bg-zinc-50 dark:bg-zinc-800 border-b border-zinc-200 dark:border-zinc-800 flex items-center justify-between">
        <div className="flex flex-col gap-1">
          <div className="flex items-center gap-2">
            <IconShoppingCart className="size-5 text-zinc-600 dark:text-zinc-400" />
            <span className="font-medium text-zinc-800 dark:text-zinc-300">
              {store}
            </span>
          </div>
          <span className="text-xs text-zinc-500 dark:text-zinc-400 ml-7">
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
              <div className="flex items-center gap-2 text-zinc-700 dark:text-zinc-300">
                <span className="text-zinc-500 dark:text-zinc-400">
                  {item.quantity}x
                </span>
                <span>{item.name}</span>
              </div>
              <span className="text-zinc-800 dark:text-zinc-200 font-medium">
                €{(item.price * item.quantity).toFixed(2)}
              </span>
            </div>
          ))}
        </div>

        {/* Price Breakdown */}
        <div className="border-t border-zinc-200 dark:border-zinc-800 pt-3 space-y-1.5">
          <div className="flex items-center justify-between text-sm text-zinc-600 dark:text-zinc-400">
            <span>Subtotal</span>
            <span>€{subtotal.toFixed(2)}</span>
          </div>
          {deliveryFee > 0 && (
            <div className="flex items-center justify-between text-sm text-zinc-600 dark:text-zinc-400">
              <span>Delivery Fee</span>
              <span>€{deliveryFee.toFixed(2)}</span>
            </div>
          )}
          {serviceFee > 0 && (
            <div className="flex items-center justify-between text-sm text-zinc-600 dark:text-zinc-400">
              <span>Service Fee</span>
              <span>€{serviceFee.toFixed(2)}</span>
            </div>
          )}
          <div className="flex items-center justify-between text-base font-semibold text-zinc-800 dark:text-zinc-200 pt-2 border-t border-zinc-200 dark:border-zinc-800">
            <span>Total</span>
            <span>€{total.toFixed(2)}</span>
          </div>
        </div>
      </div>

      {/* Delivery Time & Actions */}
      <div className="px-4 py-3 bg-zinc-50 dark:bg-zinc-800 border-t border-zinc-200 dark:border-zinc-800 flex items-center justify-between">
        <div className="flex items-center gap-2 text-sm text-zinc-600 dark:text-zinc-400">
          <IconClock className="size-4" />
          <span>Est. delivery: {estimatedDeliveryTime}</span>
        </div>
        {status === "pending" && onApprove && (
          <button
            onClick={handleApprove}
            disabled={isApproving}
            className="flex items-center gap-2 px-4 py-2 bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-900 rounded-md text-sm font-medium hover:bg-zinc-800 dark:hover:bg-zinc-200 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
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

