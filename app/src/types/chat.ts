export interface IMessage {
  id: string;
  role: MessageRole;
  content: string;
  timestamp?: Date;
}

export enum MessageRole {
  ASSISTANT = "assistant",
  USER = "user",
}
