import { ApiClient } from "./client";
import { apiBase } from "../auth/config";
import { authHeaders } from "../auth/session";
export const api = new ApiClient(apiBase, authHeaders);
