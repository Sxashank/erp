/**
 * DMS Dashboard Page
 * Overview of document management with stats, recent documents, and quick actions
 */

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  FileText,
  Folder,
  Upload,
  Search,
  Tag,
  Clock,
  HardDrive,
  TrendingUp,
  FileImage,
  FileSpreadsheet,
  FileCode,
  File,
  ChevronRight,
  RefreshCw,
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { PageHeader } from '@/components/common/PageHeader';
import { Skeleton } from '@/components/ui/skeleton';
import { documentApi } from '@/services/dmsApi';
import type { DocumentStats, DMSDocument } from '@/types/dms';
import { formatFileSize, getFileIcon } from '@/types/dms';

export default function DMSDashboard() {
  const navigate = useNavigate();
  const [stats, setStats] = useState<DocumentStats | null>(null);
  const [recentDocs, setRecentDocs] = useState<DMSDocument[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchData = async () => {
    try {
      const [statsData, recentData] = await Promise.all([
        documentApi.getStats(),
        documentApi.getRecent(10),
      ]);
      setStats(statsData);
      setRecentDocs(recentData);
    } catch (error) {
      console.error('Failed to fetch DMS data:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleRefresh = () => {
    setRefreshing(true);
    fetchData();
  };

  const getIconForExtension = (ext: string) => {
    if (['jpg', 'jpeg', 'png', 'gif', 'svg', 'webp'].includes(ext)) {
      return <FileImage className="h-5 w-5 text-green-500" />;
    }
    if (['xlsx', 'xls', 'csv'].includes(ext)) {
      return <FileSpreadsheet className="h-5 w-5 text-emerald-500" />;
    }
    if (['pdf'].includes(ext)) {
      return <FileText className="h-5 w-5 text-red-500" />;
    }
    if (['js', 'ts', 'py', 'java', 'json', 'xml', 'html', 'css'].includes(ext)) {
      return <FileCode className="h-5 w-5 text-purple-500" />;
    }
    return <File className="h-5 w-5 text-gray-500" />;
  };

  if (loading) {
    return (
      <div className="space-y-6 p-6">
        <Skeleton className="h-8 w-64" />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <Skeleton key={i} className="h-32" />
          ))}
        </div>
        <Skeleton className="h-96" />
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6">
      <PageHeader
        title="Document Management"
        subtitle="Manage, organize, and search your documents"
        actions={
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={handleRefresh} disabled={refreshing}>
              <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
            <Button onClick={() => navigate('/admin/dms/upload')}>
              <Upload className="h-4 w-4 mr-2" />
              Upload Document
            </Button>
          </div>
        }
      />

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Total Documents</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.total_documents || 0}</div>
            <p className="text-xs text-muted-foreground">
              Across all folders
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Total Folders</CardTitle>
            <Folder className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.total_folders || 0}</div>
            <p className="text-xs text-muted-foreground">
              Organization structure
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Storage Used</CardTitle>
            <HardDrive className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {stats?.total_size_mb?.toFixed(2) || 0} MB
            </div>
            <p className="text-xs text-muted-foreground">
              {formatFileSize(stats?.total_size_bytes || 0)}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Document Types</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {Object.keys(stats?.by_type || {}).length}
            </div>
            <p className="text-xs text-muted-foreground">
              Different categories
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Button
          variant="outline"
          className="h-20 flex flex-col items-center justify-center gap-2"
          onClick={() => navigate('/admin/dms/folders')}
        >
          <Folder className="h-6 w-6" />
          <span>Browse Folders</span>
        </Button>
        <Button
          variant="outline"
          className="h-20 flex flex-col items-center justify-center gap-2"
          onClick={() => navigate('/admin/dms/upload')}
        >
          <Upload className="h-6 w-6" />
          <span>Upload Document</span>
        </Button>
        <Button
          variant="outline"
          className="h-20 flex flex-col items-center justify-center gap-2"
          onClick={() => navigate('/admin/dms/search')}
        >
          <Search className="h-6 w-6" />
          <span>Search Documents</span>
        </Button>
        <Button
          variant="outline"
          className="h-20 flex flex-col items-center justify-center gap-2"
          onClick={() => navigate('/admin/dms/tags')}
        >
          <Tag className="h-6 w-6" />
          <span>Manage Tags</span>
        </Button>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Documents */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <Clock className="h-5 w-5" />
                  Recent Documents
                </CardTitle>
                <CardDescription>Recently accessed documents</CardDescription>
              </div>
              <Button variant="ghost" size="sm" onClick={() => navigate('/admin/dms/search')}>
                View All
                <ChevronRight className="h-4 w-4 ml-1" />
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {recentDocs.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <FileText className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>No documents yet</p>
                <Button
                  variant="outline"
                  size="sm"
                  className="mt-4"
                  onClick={() => navigate('/admin/dms/upload')}
                >
                  Upload your first document
                </Button>
              </div>
            ) : (
              <div className="space-y-3">
                {recentDocs.map((doc) => (
                  <div
                    key={doc.id}
                    className="flex items-center gap-3 p-3 rounded-lg border hover:bg-accent cursor-pointer transition-colors"
                    onClick={() => navigate(`/admin/dms/documents/${doc.id}`)}
                  >
                    {getIconForExtension(doc.file_extension || '')}
                    <div className="flex-1 min-w-0">
                      <p className="font-medium truncate">{doc.name}</p>
                      <p className="text-xs text-muted-foreground">
                        {formatFileSize(doc.file_size)} • {doc.file_extension?.toUpperCase()}
                      </p>
                    </div>
                    <div className="text-right">
                      <Badge variant="outline" className="text-xs">
                        v{doc.current_version}
                      </Badge>
                      <p className="text-xs text-muted-foreground mt-1">
                        {new Date(doc.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Storage by Type */}
        <Card>
          <CardHeader>
            <CardTitle>Documents by Type</CardTitle>
            <CardDescription>Distribution of document types</CardDescription>
          </CardHeader>
          <CardContent>
            {stats?.by_type && Object.keys(stats.by_type).length > 0 ? (
              <div className="space-y-4">
                {Object.entries(stats.by_type)
                  .sort(([, a], [, b]) => b - a)
                  .slice(0, 8)
                  .map(([type, count]) => (
                    <div key={type} className="flex items-center gap-3">
                      <div className="flex-1">
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-sm font-medium capitalize">
                            {type || 'Uncategorized'}
                          </span>
                          <span className="text-sm text-muted-foreground">{count}</span>
                        </div>
                        <div className="w-full bg-secondary rounded-full h-2">
                          <div
                            className="bg-primary h-2 rounded-full transition-all"
                            style={{
                              width: `${(count / (stats?.total_documents || 1)) * 100}%`,
                            }}
                          />
                        </div>
                      </div>
                    </div>
                  ))}
              </div>
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                <p>No data available</p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* By Extension */}
        <Card>
          <CardHeader>
            <CardTitle>File Extensions</CardTitle>
            <CardDescription>Top file types by extension</CardDescription>
          </CardHeader>
          <CardContent>
            {stats?.by_extension && Object.keys(stats.by_extension).length > 0 ? (
              <div className="flex flex-wrap gap-2">
                {Object.entries(stats.by_extension)
                  .sort(([, a], [, b]) => b - a)
                  .slice(0, 10)
                  .map(([ext, count]) => (
                    <Badge key={ext} variant="secondary" className="text-sm">
                      .{ext || 'unknown'} ({count})
                    </Badge>
                  ))}
              </div>
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                <p>No data available</p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* By Status */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Document Status</CardTitle>
            <CardDescription>Documents by their current status</CardDescription>
          </CardHeader>
          <CardContent>
            {stats?.by_status && Object.keys(stats.by_status).length > 0 ? (
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {Object.entries(stats.by_status).map(([status, count]) => (
                  <div
                    key={status}
                    className="p-4 rounded-lg border text-center"
                  >
                    <div className="text-2xl font-bold">{count}</div>
                    <div className="text-sm text-muted-foreground capitalize">
                      {status.replace('_', ' ')}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                <p>No status data available</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
