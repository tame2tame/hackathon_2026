import type { Me } from "../api/types";
import { RatingPage, StatsPage } from "./Analytics";
import { ReportsPage } from "./Reports";
import { ImportPage } from "./Import";
import { TeamPage } from "./Team";
import { IntegrationsPage } from "./Integrations";
import { AccessPage, AuditPage, SettingsPage } from "./Admin";
import { WorkflowsPage } from "./Workflows";
import { CatalogsPage } from "./Catalogs";
export function ServicePage({ path, me }: { path: string; me: Me }) {
  switch (path) {
    case "/analytics/rating":
      return <RatingPage me={me} />;
    case "/analytics/stats":
      return <StatsPage />;
    case "/reports":
      return <ReportsPage />;
    case "/import":
      return <ImportPage />;
    case "/team":
      return <TeamPage />;
    case "/admin/integrations":
      return <IntegrationsPage me={me} />;
    case "/admin/access":
      return <AccessPage />;
    case "/admin/audit":
      return <AuditPage />;
    case "/admin/settings":
      return <SettingsPage />;
    case "/admin/workflows":
      return <WorkflowsPage me={me} />;
    case "/admin/catalogs":
      return <CatalogsPage me={me} />;
    default:
      return null;
  }
}
