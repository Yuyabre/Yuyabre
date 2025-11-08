export interface User {
  id: string;
  name: string;
  email: string;
  avatar?: string;
  isAdmin: boolean;
}

export interface Flatmate extends User {
  joinedAt: string;
}

export interface Group {
  id: string;
  name: string;
  members: Flatmate[];
  createdAt: string;
}

export interface UserSession {
  user: User;
  group: Group;
  token: string;
}

