/**
 * LifecycleTimeline — single reusable timeline component for application +
 * loan-account history. Used by both admin LMS and borrower portal.
 *
 * Reads a `LifecycleTimelineResponse` shape and renders events grouped by
 * lifecycle phase (application → sanction → disbursement → servicing →
 * closure). Each row shows actor, timestamp, state transition, payload
 * highlights, attachments, and regulatory tags.
 */

import {
  AlertCircle,
  ArrowRight,
  Building2,
  CheckCircle2,
  Clock,
  FileText,
  Landmark,
  User as UserIcon,
  Zap,
} from 'lucide-react';

import { DateDisplay } from '@/components/common/DateDisplay';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';

export type LifecycleActorKind = 'LENDER' | 'BORROWER' | 'SYSTEM' | 'EXTERNAL';

export interface LifecycleEvent {
  id: string;
  eventAt: string;
  actorUserId?: string | null;
  actorRole?: string | null;
  actorKind: LifecycleActorKind;
  subjectType: string;
  subjectId: string;
  businessNumber?: string | null;
  eventType: string;
  stateFrom?: string | null;
  stateTo?: string | null;
  reasonCode?: string | null;
  reasonText?: string | null;
  payload?: Record<string, unknown>;
  attachments?: { dmsDocumentId?: string; fileName?: string }[];
  regulatoryTags?: string[];
  borrowerVisible: boolean;
  correlationId?: string | null;
}

interface Props {
  events: LifecycleEvent[];
  emptyText?: string;
}

function actorIcon(kind: LifecycleActorKind) {
  switch (kind) {
    case 'BORROWER':
      return <Building2 className="h-4 w-4 text-blue-600" />;
    case 'LENDER':
      return <Landmark className="h-4 w-4 text-emerald-600" />;
    case 'SYSTEM':
      return <Zap className="h-4 w-4 text-amber-600" />;
    case 'EXTERNAL':
      return <UserIcon className="h-4 w-4 text-purple-600" />;
    default:
      return <UserIcon className="h-4 w-4 text-gray-500" />;
  }
}

function eventTypeIcon(eventType: string) {
  if (eventType.includes('REJECTED') || eventType.includes('BOUNCED'))
    return <AlertCircle className="h-4 w-4 text-red-600" />;
  if (
    eventType.startsWith('CLOSED_') ||
    eventType.includes('COMPLETED') ||
    eventType.includes('APPROVED') ||
    eventType.includes('ACKNOWLEDGED')
  )
    return <CheckCircle2 className="h-4 w-4 text-emerald-600" />;
  if (eventType.includes('ISSUED') || eventType.includes('CERT'))
    return <FileText className="h-4 w-4 text-blue-600" />;
  return <Clock className="h-4 w-4 text-gray-500" />;
}

function humanise(code: string) {
  return code
    .replace(/_/g, ' ')
    .toLowerCase()
    .replace(/^./, (c) => c.toUpperCase());
}

const PHASE_ORDER: { key: string; label: string; subjects: string[] }[] = [
  { key: 'application', label: 'Application', subjects: ['APPLICATION'] },
  { key: 'sanction', label: 'Sanction', subjects: ['SANCTION'] },
  {
    key: 'disbursement',
    label: 'Disbursement',
    subjects: ['DISBURSEMENT', 'LOAN_ACCOUNT'],
  },
  {
    key: 'servicing',
    label: 'Servicing',
    subjects: ['RECEIPT', 'RESTRUCTURE', 'OTS', 'NACH_MANDATE', 'RATE_RESET'],
  },
  {
    key: 'closure',
    label: 'Closure & legal',
    subjects: [
      'LEGAL_CASE',
      'WRITE_OFF',
      'INTEREST_REVIVAL',
      'TAKEOVER',
      'TRANSFER_OUT',
      'CERTIFICATE',
    ],
  },
];

export function LifecycleTimeline({ events, emptyText = 'No events yet.' }: Props) {
  if (!events.length) {
    return (
      <div className="rounded-lg border border-dashed border-gray-300 p-6 text-center text-sm text-muted-foreground">
        {emptyText}
      </div>
    );
  }

  const phaseMap = new Map<string, LifecycleEvent[]>();
  PHASE_ORDER.forEach((p) => phaseMap.set(p.key, []));
  for (const e of events) {
    const phase = PHASE_ORDER.find((p) => p.subjects.includes(e.subjectType));
    const key = phase?.key ?? 'other';
    if (!phaseMap.has(key)) phaseMap.set(key, []);
    phaseMap.get(key)!.push(e);
  }

  return (
    <div className="space-y-6">
      {PHASE_ORDER.map((phase) => {
        const rows = phaseMap.get(phase.key) ?? [];
        if (!rows.length) return null;
        return (
          <div key={phase.key}>
            <div className="mb-2 flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              <span>{phase.label}</span>
              <span className="rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-700">
                {rows.length}
              </span>
            </div>
            <div className="space-y-2">
              {rows.map((e) => (
                <Card key={e.id} className="border-gray-200">
                  <CardContent className="py-3">
                    <div className="flex items-start gap-3">
                      <div className="mt-0.5 shrink-0">{eventTypeIcon(e.eventType)}</div>
                      <div className="min-w-0 flex-1">
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="text-sm font-medium">{humanise(e.eventType)}</span>
                          {e.stateFrom && e.stateTo ? (
                            <span className="inline-flex items-center gap-1 rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-700">
                              {e.stateFrom}
                              <ArrowRight className="h-3 w-3" />
                              {e.stateTo}
                            </span>
                          ) : e.stateTo ? (
                            <span className="rounded-full bg-emerald-50 px-2 py-0.5 text-xs text-emerald-700">
                              {e.stateTo}
                            </span>
                          ) : null}
                          {e.regulatoryTags?.map((t) => (
                            <Badge key={t} variant="outline" className="text-xs">
                              {t}
                            </Badge>
                          ))}
                        </div>
                        {e.reasonText ? (
                          <p className="mt-1 whitespace-pre-line text-sm text-gray-700">
                            {e.reasonText}
                          </p>
                        ) : null}
                        {e.attachments && e.attachments.length > 0 ? (
                          <div className="mt-2 flex flex-wrap gap-2">
                            {e.attachments.map((a, i) => (
                              <span
                                key={`${e.id}:${i}`}
                                className="inline-flex items-center gap-1 rounded-full bg-blue-50 px-2 py-0.5 text-xs text-blue-700"
                              >
                                <FileText className="h-3 w-3" />
                                {a.fileName ?? 'Attachment'}
                              </span>
                            ))}
                          </div>
                        ) : null}
                        <div className="mt-2 flex items-center gap-2 text-xs text-muted-foreground">
                          {actorIcon(e.actorKind)}
                          <span>{e.actorRole ?? e.actorKind}</span>
                          <span>•</span>
                          <DateDisplay date={e.eventAt} />
                          {e.businessNumber ? (
                            <>
                              <span>•</span>
                              <span className="font-mono">{e.businessNumber}</span>
                            </>
                          ) : null}
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}
