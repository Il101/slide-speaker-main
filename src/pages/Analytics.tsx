/**
 * Analytics Dashboard Page (Admin Only)
 */
import { useState, useEffect } from 'react';
import { Line, Bar, Doughnut } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  ChartOptions
} from 'chart.js';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { TrendingUp, Users, DollarSign, BookOpen, AlertTriangle, CheckCircle, Info } from 'lucide-react';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend
);

interface AnalyticsData {
  overview: {
    totalUsers: number;
    activeUsers: number;
    mrr: number;
    mrrGrowth: number;
    userGrowth: string;
    totalLectures: number;
    conversionRate: number;
  };
  charts: {
    userGrowth: { labels: string[]; data: number[] };
    revenue: { labels: string[]; data: number[] };
    lectureActivity: { labels: string[]; data: number[] };
    planDistribution: number[];
  };
  funnel: Array<{ step: string; count: number; rate: number; isLast: boolean }>;
  topEvents: Array<{ name: string; count: number }>;
  acquisition: Array<{ source: string; count: number; percentage: number }>;
  costs: {
    total: number;
    perUser: number;
    perLecture: number;
    margin: number;
    breakdown: {
      ocr: number;
      ai: number;
      tts: number;
      storage: number;
      other: number;
    };
  };
  insights: Array<{
    type: 'warning' | 'success' | 'info';
    title: string;
    description: string;
    action?: string;
  }>;
}

type TimeRange = '7d' | '30d' | '90d';

export default function AnalyticsPage() {
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [timeRange, setTimeRange] = useState<TimeRange>('30d');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchAnalytics();
  }, [timeRange]);

  const fetchAnalytics = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`/api/analytics/admin/dashboard?time_range=${timeRange}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch analytics');
      }

      const analyticsData = await response.json();
      setData(analyticsData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      console.error('Analytics fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading analytics...</p>
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Card className="w-96">
          <CardHeader>
            <CardTitle className="text-destructive">Error Loading Analytics</CardTitle>
            <CardDescription>{error || 'Unknown error occurred'}</CardDescription>
          </CardHeader>
          <CardContent>
            <Button onClick={fetchAnalytics}>Retry</Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Chart configurations
  const lineChartOptions: ChartOptions<'line'> = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false,
      },
    },
  };

  const barChartOptions: ChartOptions<'bar'> = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false,
      },
    },
  };

  return (
    <div className="min-h-screen bg-background p-8">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-4xl font-bold">Analytics Dashboard</h1>
            <p className="text-muted-foreground mt-2">Monitor your application's performance and growth</p>
          </div>
          
          {/* Time Range Selector */}
          <div className="flex gap-2">
            {(['7d', '30d', '90d'] as TimeRange[]).map((range) => (
              <Button
                key={range}
                variant={timeRange === range ? 'default' : 'outline'}
                onClick={() => setTimeRange(range)}
              >
                Last {range}
              </Button>
            ))}
          </div>
        </div>

        {/* Key Metrics Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <MetricCard
            title="Total Users"
            value={data.overview.totalUsers.toLocaleString()}
            change={data.overview.userGrowth}
            icon={<Users className="h-6 w-6" />}
          />
          <MetricCard
            title="MRR"
            value={`$${data.overview.mrr.toLocaleString()}`}
            change={`${data.overview.mrrGrowth >= 0 ? '+' : ''}${data.overview.mrrGrowth}%`}
            icon={<DollarSign className="h-6 w-6" />}
          />
          <MetricCard
            title="Lectures Created"
            value={data.overview.totalLectures.toLocaleString()}
            subtitle="This period"
            icon={<BookOpen className="h-6 w-6" />}
          />
          <MetricCard
            title="Conversion Rate"
            value={`${data.overview.conversionRate}%`}
            subtitle="Free → Paid"
            icon={<TrendingUp className="h-6 w-6" />}
          />
        </div>

        {/* Tabs for different views */}
        <Tabs defaultValue="overview" className="space-y-6">
          <TabsList>
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="costs">Costs</TabsTrigger>
            <TabsTrigger value="funnel">Funnel</TabsTrigger>
            <TabsTrigger value="insights">Insights</TabsTrigger>
          </TabsList>

          {/* Overview Tab */}
          <TabsContent value="overview" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* User Growth Chart */}
              <Card>
                <CardHeader>
                  <CardTitle>User Growth</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="h-64">
                    <Line
                      data={{
                        labels: data.charts.userGrowth.labels,
                        datasets: [
                          {
                            label: 'Total Users',
                            data: data.charts.userGrowth.data,
                            borderColor: 'rgb(59, 130, 246)',
                            backgroundColor: 'rgba(59, 130, 246, 0.1)',
                            tension: 0.4,
                          },
                        ],
                      }}
                      options={lineChartOptions}
                    />
                  </div>
                </CardContent>
              </Card>

              {/* Revenue Chart */}
              <Card>
                <CardHeader>
                  <CardTitle>Revenue (MRR)</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="h-64">
                    <Line
                      data={{
                        labels: data.charts.revenue.labels,
                        datasets: [
                          {
                            label: 'MRR',
                            data: data.charts.revenue.data,
                            borderColor: 'rgb(34, 197, 94)',
                            backgroundColor: 'rgba(34, 197, 94, 0.1)',
                            tension: 0.4,
                          },
                        ],
                      }}
                      options={lineChartOptions}
                    />
                  </div>
                </CardContent>
              </Card>

              {/* Lecture Activity Chart */}
              <Card>
                <CardHeader>
                  <CardTitle>Lecture Activity</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="h-64">
                    <Bar
                      data={{
                        labels: data.charts.lectureActivity.labels,
                        datasets: [
                          {
                            label: 'Lectures Created',
                            data: data.charts.lectureActivity.data,
                            backgroundColor: 'rgba(147, 51, 234, 0.5)',
                          },
                        ],
                      }}
                      options={barChartOptions}
                    />
                  </div>
                </CardContent>
              </Card>

              {/* Plan Distribution */}
              <Card>
                <CardHeader>
                  <CardTitle>Plan Distribution</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="h-64">
                    <Doughnut
                      data={{
                        labels: ['Free', 'Starter', 'Pro', 'Business'],
                        datasets: [
                          {
                            data: data.charts.planDistribution,
                            backgroundColor: [
                              'rgba(156, 163, 175, 0.5)',
                              'rgba(59, 130, 246, 0.5)',
                              'rgba(147, 51, 234, 0.5)',
                              'rgba(234, 179, 8, 0.5)',
                            ],
                          },
                        ],
                      }}
                      options={{
                        responsive: true,
                        maintainAspectRatio: false,
                      }}
                    />
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Top Events and Acquisition */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle>Top Events</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {data.topEvents.map((event, idx) => (
                      <div key={idx} className="flex justify-between items-center">
                        <span className="text-sm">{event.name}</span>
                        <span className="font-semibold">{event.count.toLocaleString()}</span>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>User Acquisition</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {data.acquisition.map((source, idx) => (
                      <div key={idx} className="space-y-1">
                        <div className="flex justify-between items-center text-sm">
                          <span>{source.source}</span>
                          <span className="font-semibold">{source.count}</span>
                        </div>
                        <div className="w-full bg-secondary rounded-full h-2">
                          <div
                            className="bg-primary h-2 rounded-full transition-all"
                            style={{ width: `${source.percentage}%` }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Costs Tab */}
          <TabsContent value="costs">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle>Cost Overview</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm text-muted-foreground">Total Costs</p>
                      <p className="text-2xl font-bold">${data.costs.total.toFixed(2)}</p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">Cost per User</p>
                      <p className="text-2xl font-bold">${data.costs.perUser.toFixed(3)}</p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">Cost per Lecture</p>
                      <p className="text-2xl font-bold">${data.costs.perLecture.toFixed(3)}</p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">Gross Margin</p>
                      <p className="text-2xl font-bold text-green-600">{data.costs.margin}%</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Cost Breakdown</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="h-64">
                    <Bar
                      data={{
                        labels: ['OCR', 'AI Generation', 'TTS', 'Storage', 'Other'],
                        datasets: [
                          {
                            label: 'Cost ($)',
                            data: [
                              data.costs.breakdown.ocr,
                              data.costs.breakdown.ai,
                              data.costs.breakdown.tts,
                              data.costs.breakdown.storage,
                              data.costs.breakdown.other,
                            ],
                            backgroundColor: 'rgba(59, 130, 246, 0.5)',
                          },
                        ],
                      }}
                      options={barChartOptions}
                    />
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Funnel Tab */}
          <TabsContent value="funnel">
            <Card>
              <CardHeader>
                <CardTitle>Conversion Funnel</CardTitle>
                <CardDescription>Track user journey from signup to paid conversion</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-6">
                  {data.funnel.map((step, idx) => (
                    <div key={idx}>
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex-1">
                          <p className="font-medium">{step.step}</p>
                          <div className="w-full bg-secondary rounded-full h-3 mt-2">
                            <div
                              className="bg-primary h-3 rounded-full transition-all"
                              style={{ width: `${step.rate}%` }}
                            />
                          </div>
                        </div>
                        <div className="ml-6 text-right">
                          <p className="text-2xl font-bold">{step.count.toLocaleString()}</p>
                          <p className="text-sm text-muted-foreground">{step.rate}%</p>
                        </div>
                      </div>
                      {!step.isLast && (
                        <div className="flex justify-center my-2">
                          <svg className="w-6 h-6 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                          </svg>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Insights Tab */}
          <TabsContent value="insights">
            <Card>
              <CardHeader>
                <CardTitle>AI Insights & Recommendations</CardTitle>
                <CardDescription>Automated insights based on your metrics</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {data.insights.map((insight, idx) => (
                    <div
                      key={idx}
                      className={`p-4 rounded-lg border-l-4 ${
                        insight.type === 'warning'
                          ? 'bg-yellow-50 border-yellow-400 dark:bg-yellow-900/20'
                          : insight.type === 'success'
                          ? 'bg-green-50 border-green-400 dark:bg-green-900/20'
                          : 'bg-blue-50 border-blue-400 dark:bg-blue-900/20'
                      }`}
                    >
                      <div className="flex items-start gap-3">
                        {insight.type === 'warning' && <AlertTriangle className="h-5 w-5 text-yellow-600 mt-0.5" />}
                        {insight.type === 'success' && <CheckCircle className="h-5 w-5 text-green-600 mt-0.5" />}
                        {insight.type === 'info' && <Info className="h-5 w-5 text-blue-600 mt-0.5" />}
                        <div className="flex-1">
                          <h4 className="font-semibold mb-1">{insight.title}</h4>
                          <p className="text-sm text-muted-foreground">{insight.description}</p>
                          {insight.action && (
                            <p className="text-sm font-medium mt-2 text-primary">→ {insight.action}</p>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}

// Helper Component
interface MetricCardProps {
  title: string;
  value: string;
  change?: string;
  subtitle?: string;
  icon: React.ReactNode;
}

function MetricCard({ title, value, change, subtitle, icon }: MetricCardProps) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">{title}</CardTitle>
        <div className="text-muted-foreground">{icon}</div>
      </CardHeader>
      <CardContent>
        <div className="text-3xl font-bold">{value}</div>
        {change && (
          <p className={`text-sm mt-2 ${change.startsWith('+') || !change.startsWith('-') ? 'text-green-600' : 'text-red-600'}`}>
            {change} vs last period
          </p>
        )}
        {subtitle && <p className="text-sm text-muted-foreground mt-2">{subtitle}</p>}
      </CardContent>
    </Card>
  );
}
