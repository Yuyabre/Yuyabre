"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { IconRobotFace, IconUser } from "@tabler/icons-react";
import { Markdown } from "./Markdown";
import { OrderCard } from "./OrderCard";
import type { IMessage } from "@/types/chat";
import { MessageRole, MessageType } from "@/types/chat";
import { ordersApi } from "@/lib/api";

export const TextStreamMessage = ({ content }: { content: string }) => {
  return (
    <motion.div
      className={`flex flex-row gap-4 px-4 w-full md:w-[500px] md:px-0 first-of-type:pt-20`}
      initial={{ y: 5, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
    >
      <div className="size-[24px] flex flex-col justify-center items-center flex-shrink-0 text-muted-foreground">
        <IconRobotFace />
      </div>

      <div className="flex flex-col gap-1 w-full">
        <div className="text-foreground flex flex-col gap-4">
          <Markdown>{content}</Markdown>
        </div>
      </div>
    </motion.div>
  );
};

interface MessageProps extends IMessage {
  onOrderApproved?: (
    message: string,
    updatedOrder: IMessage["orderData"]
  ) => void;
}

export const Message = ({
  id,
  role,
  type,
  content,
  orderData,
  onOrderApproved,
}: MessageProps) => {
  const [currentOrderData, setCurrentOrderData] = useState(orderData);

  const handleApprove = async () => {
    if (!currentOrderData) return;

    try {
      // Convert orderData to Order format for the API
      const orderDataForApi = {
        service: currentOrderData.service,
        store: currentOrderData.store,
        items: currentOrderData.items,
        total: currentOrderData.total,
      };

      const { order, message } = await ordersApi.approve(
        currentOrderData.id,
        orderDataForApi
      );

      // Update the order data with the new status
      const updatedOrderData = {
        ...currentOrderData,
        status: order.status as
          | "pending"
          | "preparing"
          | "delivering"
          | "delivered",
      };
      setCurrentOrderData(updatedOrderData);

      // Notify parent to add a follow-up message
      if (onOrderApproved) {
        onOrderApproved(message, updatedOrderData);
      }
    } catch (error) {
      console.error("Failed to approve order:", error);
      // You could show an error message here
    }
  };

  return (
    <motion.div
      className={`flex flex-row gap-4 px-4 w-full md:w-[500px] md:px-0 first-of-type:pt-20`}
      initial={{ y: 5, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      key={id}
    >
      <div className="size-[24px] flex flex-col justify-center items-center flex-shrink-0 text-muted-foreground">
        {role === MessageRole.ASSISTANT ? <IconRobotFace /> : <IconUser />}
      </div>

      <div className="flex flex-col gap-1 w-full">
        {type === MessageType.ORDER && currentOrderData ? (
          <div className="flex flex-col gap-4">
            {content && (
              <div className="text-foreground">
                <Markdown>{content}</Markdown>
              </div>
            )}
            <OrderCard
              id={currentOrderData.id}
              service={currentOrderData.service}
              store={currentOrderData.store}
              items={currentOrderData.items}
              subtotal={currentOrderData.subtotal}
              deliveryFee={currentOrderData.deliveryFee}
              serviceFee={currentOrderData.serviceFee}
              total={currentOrderData.total}
              estimatedDeliveryTime={currentOrderData.estimatedDeliveryTime}
              status={currentOrderData.status}
              onApprove={handleApprove}
              onStatusUpdate={(newStatus) => {
                setCurrentOrderData((prev) =>
                  prev ? { ...prev, status: newStatus } : undefined
                );
              }}
            />
          </div>
        ) : (
          <div className="text-foreground flex flex-col gap-4">
            <Markdown>{content}</Markdown>
          </div>
        )}
      </div>
    </motion.div>
  );
};
