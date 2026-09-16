import type { components, paths } from "./schema";
export type Schema = components["schemas"];
export type Me = Schema["MeOut"];
export type Interaction = Schema["InteractionDetail"];
export type InteractionItem = Schema["InteractionListItem"];
export type Signal = Schema["SignalListItem"];
export type University = Schema["UniversityOut"];
export type Workflow = Schema["WorkflowOut"];
export type Transition = Schema["TransitionCreate"];
export type Role = Schema["Role"];
export type InteractionFilters = NonNullable<
  paths["/api/v1/interactions"]["get"]["parameters"]["query"]
>;
export type SignalFilters = NonNullable<
  paths["/api/v1/signals"]["get"]["parameters"]["query"]
>;
export type UniversityFilters = NonNullable<
  paths["/api/v1/universities"]["get"]["parameters"]["query"]
>;
