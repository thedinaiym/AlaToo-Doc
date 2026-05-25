export type UserRole = "student" | "teacher" | "dean" | "admin";

export type DocumentStatus = "draft" | "pending" | "signed" | "rejected";

export interface User {
  id: string;
  university_id: string;
  full_name: string;
  role: UserRole;
}

export interface Document {
  id: string;
  title: string;
  status: DocumentStatus;
}

export interface Signature {
  id: string;
  document_id: string;
  user_id: string;
  signature_hash: string;
  signed_at: string;
}
