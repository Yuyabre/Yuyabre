export interface UserPreferenceRequest {
  dietary_restrictions?: string[];
  allergies?: string[];
  favorite_brands?: string[];
  disliked_items?: string[];
}

export interface SignupRequest {
  name: string;
  password: string;
  email?: string | null;
  phone?: string | null;
  discord_user_id?: string | null;
  preferences?: UserPreferenceRequest | null;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface User {
  user_id: string;
  name: string;
  email?: string | null;
  phone?: string | null;
  household_id?: string | null;
  is_active: boolean;
  joined_date: string;
}

export interface Household {
  household_id: string;
  name: string;
  invite_code: string;
  discord_channel_id?: string | null;
  whatsapp_group_id?: string | null; // Deprecated
  whatsapp_group_name?: string | null; // Deprecated
  address?: string | null;
  city?: string | null;
  postal_code?: string | null;
  country?: string | null;
  notes?: string | null;
  member_ids: string[];
  created_at: string;
  is_active: boolean;
}

export interface CreateHouseholdRequest {
  name: string;
  discord_channel_id?: string | null;
  address?: string | null;
  city?: string | null;
  postal_code?: string | null;
  country?: string | null;
  notes?: string | null;
}

export interface JoinHouseholdRequest {
  invite_code: string;
}

