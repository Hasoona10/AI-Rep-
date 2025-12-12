'use client';

import React, { useEffect, useMemo, useState } from 'react';
import {
  Tabs,
  TabsList,
  TabsTrigger,
  TabsContent,
} from '@/components/ui/tabs';
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from '@/components/ui/card';
import {
  Select,
  SelectTrigger,
  SelectValue,
  SelectContent,
  SelectItem,
} from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Switch } from '@/components/ui/switch';
import { Separator } from '@/components/ui/separator';
import {
  PhoneCall,
  Receipt,
  AlertTriangle,
  DollarSign,
  Brain,
  Search,
  Filter,
  Sun,
  Moon,
  Sparkles,
  LineChart as LineChartIcon,
  PieChart,
  BarChart3,
  Gauge,
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  ResponsiveContainer,
  Pie,
  PieChart as RePieChart,
  Cell,
  BarChart,
  Bar,
  Legend,
} from 'recharts';
import clsx from 'clsx';
import dayjs from 'dayjs';

type CallLog = {
  timeUtc: string;
  callSid: string;
  intent: 'menu' | 'greeting' | 'direction' | 'general_question' | 'unknown' | string;
  customerSaid: string;
  orderItems: string | null;
  orderTotal: string | null;
  responseSource: string;
  aiResponse: string;
};

const mockCallLogs: CallLog[] = [
  {
    timeUtc: '2025-12-11T00:15:52.964418Z',
    callSid: 'ws_2ca6973bfbb7',
    intent: 'menu',
    customerSaid: '3 chicken shawarma sandwiches, 1 side of fries, 1 fattouch salad, and 3 cokes',
    orderItems:
      '3 x Chicken Shawarma Wrap ($46.50); 1 x French Fries ($5.00); 1 x Fattoush ($12.00); 3 x Soft Drinks ($10.50)',
    orderTotal: '$74.00',
    responseSource: 'template_order_parsed',
    aiResponse:
      'So far I have: 3 Chicken Shawarma Wrap, 1 Fattoush, 1 French Fries, 3 Soft Drinks. The estimated total is $74.00 before tax and fees. Would you like to add anything else or is that everything?',
  },
  {
    timeUtc: '2025-12-10T23:27:16.538554Z',
    callSid: 'ws_9f038873326a',
    intent: 'menu',
    customerSaid: 'id like to make an order',
    orderItems: null,
    orderTotal: null,
    responseSource: 'template_order_prompt',
    aiResponse:
      "Absolutely! I'd be happy to help you place an order. What would you like to order today? You can tell me the items and quantities, for example, '2 chicken shawarma wraps' or 'a mixed grill plate'.",
  },
  {
    timeUtc: '2025-12-10T23:02:44.508008Z',
    callSid: 'ws_18c90a745dbe',
    intent: 'menu',
    customerSaid: 'hello id like to make an order',
    orderItems: null,
    orderTotal: null,
    responseSource: 'template_order_prompt',
    aiResponse:
      "Absolutely! I'd be happy to help you place an order. What would you like to order today? You can tell me the items and quantities, for example, '2 chicken shawarma wraps' or 'a mixed grill plate'.",
  },
  {
    timeUtc: '2025-12-10T23:01:15.002044Z',
    callSid: 'ws_a944b60e0c7b',
    intent: 'menu',
    customerSaid: '3 shawarma sandwiches, 1 beef and 2 chicken, 1 hummus plate, 1 fattoush salad, 1 fries, and 3 coke.',
    orderItems: '1 x Fattoush ($12.00)',
    orderTotal: '$12.00',
    responseSource: 'template_followup_mappings',
    aiResponse: 'I have 1 Fattoush. Would you like to add anything else?',
  },
  {
    timeUtc: '2025-12-03T10:41:22.872185Z',
    callSid: 'CA_add20613',
    intent: 'menu',
    customerSaid: 'I want to add 1, Falafel wrap.',
    orderItems: '1 x Falafel Wrap ($14.00)',
    orderTotal: '$14.00',
    responseSource: 'template_order_parsed',
    aiResponse:
      'So far I have: 1 Falafel Wrap. The estimated total is $14.00 before tax and fees. Would you like to add anything else or is that everything?',
  },
];

const intentColors: Record<string, string> = {
  menu: 'bg-emerald-100 text-emerald-700 border-emerald-200',
  greeting: 'bg-blue-100 text-blue-700 border-blue-200',
  direction: 'bg-amber-100 text-amber-700 border-amber-200',
  general_question: 'bg-slate-100 text-slate-700 border-slate-200',
  unknown: 'bg-gray-100 text-gray-700 border-gray-200',
};

const responseSourceLabels: Record<string, string> = {
  template_order_parsed: 'Template (order parsed)',
  template_order_prompt: 'Template (order prompt)',
  template_order_summary: 'Template (order summary)',
  template_order_repeat: 'Template (order repeat)',
  template_followup_mappings: 'Template (follow-up)',
  template_facts: 'Template (facts)',
  template_intent: 'Template (intent)',
  llm_cached: 'LLM cached',
  llm_gpt4o_mini: 'LLM generated',
  llm_inferred: 'LLM fallback used',
  template_inferred: 'Template inferred',
  unknown: 'Unclassified',
};

const sourceCategory = (source: string) => {
  if (/llm/i.test(source)) return 'llm';
  if (/template/i.test(source)) return 'template';
  return 'unknown';
};

const statusForCall = (call: CallLog) => {
  const hasOrder = !!call.orderTotal;
  const looksOrder = /order|wrap|shawarma|fries|coke|plate|salad/i.test(call.customerSaid);
  if (hasOrder) return { label: 'Parsed structured order', icon: '✅', tone: 'text-emerald-600' };
  if (looksOrder) return { label: 'Review needed', icon: '⚠️', tone: 'text-amber-600' };
  return { label: 'Informational call', icon: 'ℹ️', tone: 'text-slate-600' };
};

const formatLocalTime = (utc: string) => dayjs(utc).format('MMM D, HH:mm');
const shortSid = (sid: string) => (sid.length > 10 ? `${sid.slice(0, 6)}...${sid.slice(-4)}` : sid);
const parseOrderItems = (orderItems: string | null) => {
  if (!orderItems) return [];
  return orderItems.split(';').map((item) => {
    const trimmed = item.trim();
    const qtyMatch = trimmed.match(/^\d+/);
    const priceMatch = trimmed.match(/\$[\d,.]+/);
    const name = trimmed.replace(/^\d+\s*x\s*/i, '').replace(/\s*\([\$\d.,]+\)/, '').trim();
    return {
      raw: trimmed,
      qty: qtyMatch ? Number(qtyMatch[0]) : 1,
      name,
      price: priceMatch ? priceMatch[0] : '',
    };
  });
};

const orderTypeTag = (total: number | null, hasItems: boolean) => {
  if (total && total > 50) return { label: 'Group order', tone: 'bg-emerald-50 text-emerald-700' };
  if (total && total <= 50) return { label: 'Single order', tone: 'bg-blue-50 text-blue-700' };
  if (hasItems) return { label: 'Parsed items', tone: 'bg-indigo-50 text-indigo-700' };
  return { label: 'Potential order', tone: 'bg-amber-50 text-amber-700' };
};

const aiSummary = (call: CallLog) => {
  const hasItems = !!call.orderItems;
  const total = call.orderTotal ? Number(call.orderTotal.replace(/[^0-9.]/g, '')) : null;
  const looksOrder = /order|wrap|shawarma|fries|coke|plate|salad/i.test(call.customerSaid);
  if (hasItems && total && total > 50) return 'Likely a group or family order.';
  if (hasItems) return 'Structured order captured and ready to confirm.';
  if (!hasItems && looksOrder) return 'Order intent detected but details need review.';
  return 'Informational call with no structured order.';
};

const calcMetrics = (calls: CallLog[]) => {
  const callsToday = calls.length;
  const parsedOrders = calls.filter((c) => c.orderTotal).length;
  const needsReview = calls.filter((c) => !c.orderTotal && /order|wrap|shawarma|fries|coke|plate|salad/i.test(c.customerSaid)).length;

  // Deduplicate revenue by callSid, using the highest numeric total per call
  const totalsByCall: Record<string, number> = {};
  for (const c of calls) {
    const n = c.orderTotal ? Number((c.orderTotal || '').replace(/[^0-9.]/g, '')) : 0;
    if (n > 0) {
      const key = c.callSid || c.timeUtc;
      totalsByCall[key] = Math.max(totalsByCall[key] || 0, n);
    }
  }
  const aiRevenue = Object.values(totalsByCall).reduce((a, b) => a + b, 0);

  const llmUsed = calls.filter((c) => /llm/i.test(c.responseSource || '')).length;
  const llmRate = calls.length ? Math.round((llmUsed / calls.length) * 100) : 0;
  return { callsToday, parsedOrders, needsReview, aiRevenue, llmRate };
};

const callsOverTimeData = (calls: CallLog[]) => {
  const byDay: Record<string, number> = {};
  calls.forEach((c) => {
    const day = dayjs(c.timeUtc).format('MMM D');
    byDay[day] = (byDay[day] || 0) + 1;
  });
  return Object.entries(byDay).map(([name, value]) => ({ name, value }));
};

const parsedVsUnparsedData = (calls: CallLog[]) => {
  const parsed = calls.filter((c) => c.orderTotal).length;
  const unparsed = calls.length - parsed;
  return [
    { name: 'Parsed', value: parsed },
    { name: 'Unparsed', value: unparsed },
  ];
};

const intentDistributionData = (calls: CallLog[]) => {
  const byIntent: Record<string, number> = {};
  calls.forEach((c) => {
    byIntent[c.intent] = (byIntent[c.intent] || 0) + 1;
  });
  return Object.entries(byIntent).map(([name, value]) => ({ name, value }));
};

const llmUsageData = (calls: CallLog[]) => {
  const llm = calls.filter((c) => /llm/i.test(c.responseSource || '')).length;
  const template = calls.length - llm;
  return [
    { name: 'LLM', value: llm },
    { name: 'Template', value: template },
  ];
};

const badgeForIntent = (intent: string) => intentColors[intent] || 'bg-slate-100 text-slate-700 border-slate-200';
const badgeForSource = (source: string) => responseSourceLabels[source] || responseSourceLabels.unknown;

const friendlyIntent = (intent: string) => {
  switch (intent) {
    case 'menu':
      return 'Menu / Order';
    case 'greeting':
      return 'Greeting / Start';
    case 'direction':
      return 'Add-on / Change';
    case 'general_question':
      return 'General Inquiry';
    case 'unknown':
      return 'Unclassified';
    default:
      return intent;
  }
};

const CallListEmpty = ({ onReset }: { onReset: () => void }) => (
  <Card className="border-dashed bg-white/70 backdrop-blur-sm">
    <CardContent className="py-10 text-center space-y-3">
      <div className="text-lg font-semibold text-slate-700">No calls match these filters</div>
      <div className="text-sm text-slate-500">Try adjusting the filters or clearing the search to see more conversations.</div>
      <Button variant="outline" onClick={onReset} className="mt-2">
        Reset filters
      </Button>
    </CardContent>
  </Card>
);

export default function OwnerDashboardPage() {
  const [calls, setCalls] = useState<CallLog[]>(mockCallLogs);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [intentFilter, setIntentFilter] = useState<string>('all');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [sourceFilter, setSourceFilter] = useState<string>('all');
  const [search, setSearch] = useState<string>('');
  const [selected, setSelected] = useState<CallLog | null>(mockCallLogs[0] || null);
  const [themeDark, setThemeDark] = useState<boolean>(false);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        const apiBase = process.env.NEXT_PUBLIC_API_BASE || 'http://127.0.0.1:8000';
        const res = await fetch(`${apiBase}/api/owner/orders`, { cache: 'no-store' });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        if (Array.isArray(data) && data.length > 0) {
          const parsed: CallLog[] = data.map((o: any) => ({
            timeUtc: o.timestamp || o.timeUtc || '',
            callSid: o.call_sid || o.callSid || '',
            intent: o.intent || 'unknown',
            customerSaid: o.customer_text || o.customerSaid || '',
            orderItems: Array.isArray(o.order_items)
              ? o.order_items
                  .map((it: any) => {
                    const qty = it.quantity ?? it.qty ?? 1;
                    const name = it.name ?? 'item';
                    const price = it.total_price ?? it.line_total ?? it.unit_price ?? null;
                    const priceStr = price != null ? `$${Number(price).toFixed(2)}` : '';
                    return `${qty} x ${name}${priceStr ? ` (${priceStr})` : ''}`;
                  })
                  .join('; ')
              : o.orderItems || null,
            orderTotal:
              o.order_total != null
                ? `$${Number(o.order_total).toFixed(2)}`
                : o.orderTotal ?? null,
            responseSource: o.response_source || o.responseSource || 'unknown',
            aiResponse: o.ai_response || o.aiResponse || '',
          }));
          setCalls(parsed);
          setSelected(parsed[0] || null);
        } else {
          setCalls(mockCallLogs);
          setSelected(mockCallLogs[0] || null);
        }
      } catch (err) {
        setError((err as Error).message || 'Failed to load data');
        setCalls(mockCallLogs);
        setSelected(mockCallLogs[0] || null);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const filtered = useMemo(() => {
    return calls.filter((c) => {
      const intentOk = intentFilter === 'all' || c.intent === intentFilter;
      const status = statusForCall(c).label;
      const statusOk =
        statusFilter === 'all' ||
        (statusFilter === 'parsed' && status === 'Parsed structured order') ||
        (statusFilter === 'needs' && status === 'Review needed') ||
        (statusFilter === 'nonorder' && status === 'Informational call');
      const srcCat = sourceCategory(c.responseSource || '');
      const sourceOk =
        sourceFilter === 'all' ||
        (sourceFilter === 'llm' && srcCat === 'llm') ||
        (sourceFilter === 'template' && srcCat === 'template') ||
        (sourceFilter === 'unknown' && srcCat === 'unknown');
      const s = search.toLowerCase();
      const searchOk =
        !s ||
        c.customerSaid.toLowerCase().includes(s) ||
        c.aiResponse.toLowerCase().includes(s) ||
        c.responseSource.toLowerCase().includes(s) ||
        c.intent.toLowerCase().includes(s);
      return intentOk && statusOk && sourceOk && searchOk;
    });
  }, [calls, intentFilter, statusFilter, sourceFilter, search]);

  const metrics = calcMetrics(filtered);
  const callsOverTime = callsOverTimeData(filtered);
  const parsedVsUnparsed = parsedVsUnparsedData(filtered);
  const intentDist = intentDistributionData(filtered);
  const llmUsage = llmUsageData(filtered);

  const detail = selected || filtered[0] || null;
  const detailItems = parseOrderItems(detail?.orderItems || null);
  const detailTotal = detail?.orderTotal ? Number(detail.orderTotal.replace(/[^0-9.]/g, '')) : null;
  const detailOrderType = orderTypeTag(detailTotal, detailItems.length > 0);
  const detailSummary = detail ? aiSummary(detail) : '';

  const setTheme = (value: boolean) => setThemeDark(value);

  return (
    <div className={clsx('min-h-screen w-full', themeDark ? 'bg-slate-950 text-slate-50' : 'bg-[#F8F4ED] text-slate-900')}>
      <div className="mx-auto max-w-[1600px] px-8 py-8 space-y-8">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="h-10 w-10 rounded-xl bg-emerald-200 text-emerald-800 grid place-items-center font-bold">CG</div>
            <div>
              <div className="text-2xl font-semibold tracking-tight">AI Phone Orders</div>
              <div className="text-sm text-slate-500">
                Real-time insights into calls, orders, and AI-assisted interactions.
              </div>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Select defaultValue="last7">
              <SelectTrigger className="w-36">
                <SelectValue placeholder="Date Range" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="today">Today</SelectItem>
                <SelectItem value="last7">Last 7 days</SelectItem>
                <SelectItem value="last30">Last 30 days</SelectItem>
              </SelectContent>
            </Select>
            <div className="flex items-center gap-2 rounded-full bg-emerald-100 text-emerald-800 px-3 py-1 text-sm">
              <span className="text-emerald-500">●</span> AI Agent: Online
            </div>
            <div className="flex items-center gap-2 rounded-full bg-white/70 px-3 py-1 border border-slate-200 shadow-sm">
              <Sun className="h-4 w-4" />
              <Switch checked={themeDark} onCheckedChange={setTheme} />
              <Moon className="h-4 w-4" />
            </div>
          </div>
        </div>

        <Tabs defaultValue="overview" className="space-y-6">
          <TabsList className="bg-white/80 border border-slate-200 shadow-sm">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="analytics">Analytics</TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-5 gap-4">
                {[
                  { title: 'Calls Processed', value: metrics.callsToday, icon: PhoneCall, tone: 'from-emerald-50 to-emerald-100' },
                  { title: 'Structured Orders', value: metrics.parsedOrders, icon: Receipt, tone: 'from-blue-50 to-blue-100' },
                  { title: 'Review Needed', value: metrics.needsReview, icon: AlertTriangle, tone: 'from-amber-50 to-amber-100' },
                  { title: 'Estimated Revenue', value: `$${metrics.aiRevenue.toFixed(2)}`, icon: DollarSign, tone: 'from-indigo-50 to-indigo-100' },
                  { title: 'LLM Usage Rate', value: `${metrics.llmRate}%`, icon: Brain, tone: 'from-rose-50 to-rose-100' },
                ].map((m, i) => (
                <motion.div
                  key={m.title}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.05, duration: 0.35 }}
                >
                  <Card className={clsx('border-0 shadow-sm bg-gradient-to-br', m.tone)}>
                    <CardContent className="py-4 px-5 flex items-center justify-between">
                      <div>
                        <div className="text-sm text-slate-500">{m.title}</div>
                        <div className="text-2xl font-semibold mt-1">{m.value}</div>
                      </div>
                      <div className="h-11 w-11 rounded-xl bg-white/80 text-emerald-700 grid place-items-center shadow-sm">
                        <m.icon className="h-5 w-5" />
                      </div>
                    </CardContent>
                  </Card>
                </motion.div>
              ))}
            </div>

            <Card className="border-0 shadow-sm bg-white/80">
              <CardContent className="py-4 flex flex-wrap gap-3 items-center">
                <div className="flex items-center gap-2 text-slate-500">
                  <Filter className="h-4 w-4" />
                  <span className="text-sm font-medium">Filters</span>
                </div>
                <Select value={intentFilter} onValueChange={setIntentFilter}>
                  <SelectTrigger className="w-44 bg-white">
                    <SelectValue placeholder="Intent" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All intents</SelectItem>
                    <SelectItem value="menu">Menu / Order</SelectItem>
                    <SelectItem value="greeting">Greeting / Start</SelectItem>
                    <SelectItem value="direction">Add-on / Change</SelectItem>
                    <SelectItem value="general_question">General Inquiry</SelectItem>
                    <SelectItem value="unknown">Unclassified</SelectItem>
                  </SelectContent>
                </Select>
                <Select value={statusFilter} onValueChange={setStatusFilter}>
                  <SelectTrigger className="w-44 bg-white">
                    <SelectValue placeholder="Status" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All statuses</SelectItem>
                    <SelectItem value="parsed">Parsed structured order</SelectItem>
                    <SelectItem value="needs">Review needed</SelectItem>
                    <SelectItem value="nonorder">Informational call</SelectItem>
                  </SelectContent>
                </Select>
                <Select value={sourceFilter} onValueChange={setSourceFilter}>
                  <SelectTrigger className="w-44 bg-white">
                    <SelectValue placeholder="Source" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All sources</SelectItem>
                    <SelectItem value="template">Template only</SelectItem>
                    <SelectItem value="llm">LLM only</SelectItem>
                    <SelectItem value="unknown">Unclassified</SelectItem>
                  </SelectContent>
                </Select>
                <div className="flex-1 min-w-[260px]">
                  <div className="relative">
                    <Search className="h-4 w-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                    <Input
                      placeholder="Search customer text or AI response..."
                      className="pl-9 bg-white"
                      value={search}
                      onChange={(e) => setSearch(e.target.value)}
                    />
                  </div>
                </div>
              </CardContent>
            </Card>

            <div className="grid grid-cols-1 xl:grid-cols-12 gap-5">
              <div className="xl:col-span-5 space-y-3 max-h-[960px] overflow-auto pr-1">
                <AnimatePresence initial={false}>
                  {filtered.length === 0 ? (
                    <CallListEmpty onReset={() => { setIntentFilter('all'); setStatusFilter('all'); setSearch(''); }} />
                  ) : (
                    filtered.map((call, idx) => {
                      const status = statusForCall(call);
                      return (
                        <motion.div
                          key={call.callSid + call.timeUtc}
                          initial={{ opacity: 0, y: 8 }}
                          animate={{ opacity: 1, y: 0 }}
                          exit={{ opacity: 0, y: 8 }}
                          transition={{ delay: idx * 0.02 }}
                        >
                          <Card
                            onClick={() => setSelected(call)}
                            className={clsx(
                              'cursor-pointer border border-transparent hover:border-emerald-200 hover:shadow-md transition-all bg-white/90',
                              selected?.callSid === call.callSid ? 'ring-2 ring-emerald-200' : ''
                            )}
                          >
                            <CardContent className="p-4 space-y-2">
                              <div className="flex items-center justify-between">
                                <div className="flex items-center gap-2">
                                  <Badge className={clsx('border', badgeForIntent(call.intent))}>{friendlyIntent(call.intent)}</Badge>
                                  <span className={clsx('text-sm font-medium', status.tone)}>
                                    {status.icon} {status.label}
                                  </span>
                                </div>
                                <div className="text-sm text-slate-500">{formatLocalTime(call.timeUtc)}</div>
                              </div>
                              <div className="text-sm text-slate-800 line-clamp-2">{call.customerSaid}</div>
                              <div className="flex items-center justify-between text-xs text-slate-500">
                                <span>SID: {shortSid(call.callSid)}</span>
                                {call.orderTotal ? (
                                  <span className="font-semibold text-emerald-700">{call.orderTotal}</span>
                                ) : (
                                  <span className="text-amber-600">No structured order</span>
                                )}
                              </div>
                            </CardContent>
                          </Card>
                        </motion.div>
                      );
                    })
                  )}
                </AnimatePresence>
              </div>

              <div className="xl:col-span-7 space-y-4">
                <Card className="border-0 shadow-sm bg-white/90">
                  <CardHeader>
                    <div className="flex items-center justify-between gap-3">
                      <div>
                        <CardTitle className="text-xl">Call Detail</CardTitle>
                        <CardDescription className="text-slate-500">
                          AI interpretation and structured order details.
                        </CardDescription>
                      </div>
                      <Badge variant="outline" className="bg-emerald-50 text-emerald-700 border-emerald-200">
                        <Sparkles className="h-4 w-4 mr-1" />
                        Insight Summary
                      </Badge>
                    </div>
                  </CardHeader>
                  <Separator />
                  <CardContent className="space-y-4">
                    {detail ? (
                      <>
                        <div className="flex flex-wrap items-center justify-between gap-3">
                          <div className="space-y-1">
                            <div className="text-sm text-slate-500">{formatLocalTime(detail.timeUtc)}</div>
                            <div className="flex items-center gap-2">
                              <Badge className={clsx('border', badgeForIntent(detail.intent))}>{detail.intent}</Badge>
                              <Badge variant="outline" className="bg-slate-100 text-slate-700">
                                SID: {shortSid(detail.callSid)}
                              </Badge>
                              <Badge className={detailOrderType.tone}>{detailOrderType.label}</Badge>
                            </div>
                          </div>
                          <Badge variant="outline" className="bg-white text-slate-700 border-slate-200">
                            {badgeForSource(detail.responseSource)}
                          </Badge>
                        </div>

                        <Card className="border bg-white/70">
                          <CardHeader>
                            <CardTitle className="text-sm text-slate-600">ASR Transcript</CardTitle>
                          </CardHeader>
                          <CardContent>
                            <div className="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-800">
                              {detail.customerSaid}
                            </div>
                          </CardContent>
                        </Card>

                        <Card className="border bg-white/70">
                          <CardHeader>
                            <CardTitle className="text-sm text-slate-600">AI Interpretation</CardTitle>
                          </CardHeader>
                          <CardContent className="space-y-2">
                            <div className="flex items-center gap-2 text-sm">
                              <Badge variant="outline" className="bg-white text-slate-700 border-slate-200">
                                {badgeForSource(detail.responseSource)}
                              </Badge>
                              <span className="text-slate-600">
                                {detail.orderItems
                                  ? 'Parsed structured order'
                                  : /order|wrap|shawarma|fries|coke|plate|salad/i.test(detail.customerSaid)
                                  ? 'Review needed'
                                  : 'Informational call'}
                              </span>
                            </div>
                            <div className="text-sm text-slate-600">{detailSummary}</div>
                          </CardContent>
                        </Card>

                        <Card className="border bg-white/70">
                          <CardHeader>
                            <CardTitle className="text-sm text-slate-600">Order Summary</CardTitle>
                          </CardHeader>
                          <CardContent className="space-y-3">
                            {detailItems.length > 0 ? (
                              <>
                                <div className="space-y-2">
                                  {detailItems.map((it, idx) => (
                                    <div
                                      key={idx}
                                      className="flex items-center justify-between rounded-xl border border-slate-200 bg-white px-3 py-2"
                                    >
                                      <div className="flex items-center gap-2">
                                        <Badge className="bg-emerald-50 text-emerald-700 border-emerald-200">{it.qty}x</Badge>
                                        <div className="text-sm text-slate-800">{it.name}</div>
                                      </div>
                                      <div className="text-sm font-semibold text-slate-700">{it.price}</div>
                                    </div>
                                  ))}
                                </div>
                                <Separator />
                                <div className="flex items-center justify-between">
                                  <div className="text-sm text-slate-600">Estimated Total</div>
                                  <div className="text-lg font-semibold text-slate-800">
                                    {detail.orderTotal || '—'}
                                  </div>
                                </div>
                              </>
                            ) : (
                              <div className="text-sm text-amber-600">No structured order captured</div>
                            )}
                          </CardContent>
                        </Card>

                        <Card className="border bg-white/70">
                          <CardHeader>
                            <div className="flex items-center gap-2 text-slate-700">
                              <Brain className="h-4 w-4" />
                              <CardTitle className="text-sm">Insight Summary</CardTitle>
                            </div>
                          </CardHeader>
                          <CardContent>
                            <div className="rounded-xl border border-slate-200 bg-emerald-50/60 px-4 py-3 text-sm text-emerald-900">
                              {detailSummary}
                            </div>
                          </CardContent>
                        </Card>

                        <Card className="border bg-white/70">
                          <CardHeader>
                            <CardTitle className="text-sm text-slate-600">AI Response</CardTitle>
                          </CardHeader>
                          <CardContent>
                            <div className="rounded-xl border border-slate-200 bg-slate-900 text-slate-50 px-4 py-3 text-sm font-mono whitespace-pre-wrap">
                              {detail.aiResponse}
                            </div>
                          </CardContent>
                        </Card>
                      </>
                    ) : (
                      <div className="text-sm text-slate-500">Select a call to view details.</div>
                    )}
                  </CardContent>
                </Card>
              </div>
            </div>
          </TabsContent>

          <TabsContent value="analytics" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4">
              <Card className="border-0 shadow-sm bg-white/90">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-slate-800">
                    <LineChartIcon className="h-5 w-5 text-emerald-600" /> Calls Over Time
                  </CardTitle>
                  <CardDescription className="text-slate-500">Trend of all calls handled by the AI agent over time.</CardDescription>
                </CardHeader>
                <CardContent className="h-64">
                  <ResponsiveContainer>
                    <LineChart data={callsOverTime}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                      <XAxis dataKey="name" stroke="#94a3b8" />
                      <YAxis stroke="#94a3b8" />
                      <RechartsTooltip />
                      <Line type="monotone" dataKey="value" stroke="#10b981" strokeWidth={2} dot={{ r: 3 }} />
                    </LineChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>

              <Card className="border-0 shadow-sm bg-white/90">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-slate-800">
                    <PieChart className="h-5 w-5 text-amber-600" /> Parsed vs Unparsed
                  </CardTitle>
                  <CardDescription className="text-slate-500">Share of calls resulting in structured orders vs non-orders.</CardDescription>
                </CardHeader>
                <CardContent className="h-64">
                  <ResponsiveContainer>
                    <RePieChart>
                      <Pie data={parsedVsUnparsed} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80} label>
                        <Cell fill="#10b981" />
                        <Cell fill="#f59e0b" />
                      </Pie>
                      <RechartsTooltip />
                    </RePieChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>

              <Card className="border-0 shadow-sm bg-white/90">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-slate-800">
                    <BarChart3 className="h-5 w-5 text-indigo-600" /> Intent Distribution
                  </CardTitle>
                  <CardDescription className="text-slate-500">Distribution of detected intents.</CardDescription>
                </CardHeader>
                <CardContent className="h-64">
                  <ResponsiveContainer>
                    <BarChart data={intentDist}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                      <XAxis dataKey="name" stroke="#94a3b8" />
                      <YAxis stroke="#94a3b8" />
                      <RechartsTooltip />
                      <Bar dataKey="value" fill="#6366f1" radius={[6, 6, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>

              <Card className="border-0 shadow-sm bg-white/90 xl:col-span-3">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-slate-800">
                    <Gauge className="h-5 w-5 text-rose-600" /> LLM Fallback Usage
                  </CardTitle>
                  <CardDescription className="text-slate-500">How often the system used LLM fallback vs template responses.</CardDescription>
                </CardHeader>
                <CardContent className="h-64">
                  <ResponsiveContainer>
                    <BarChart data={llmUsage}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                      <XAxis dataKey="name" stroke="#94a3b8" />
                      <YAxis stroke="#94a3b8" />
                      <RechartsTooltip />
                      <Legend />
                      <Bar dataKey="value" fill="#f43f5e" radius={[6, 6, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}

