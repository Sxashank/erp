/**
 * Document Versions Page
 * Manage document versions, upload new versions, compare versions
 */

import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useDropzone } from 'react-dropzone';
import {
  FileText,
  Upload,
  Download,
  ArrowLeft,
  Check,
  Clock,
  User,
  Loader2,
  File,
  FileImage,
  FileSpreadsheet,
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Progress } from '@/components/ui/progress';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { useToast } from '@/hooks/use-toast';
import { documentApi } from '@/services/dmsApi';
import type { DMSDocument, DocumentVersion } from '@/types/dms';
import { formatFileSize } from '@/types/dms';

export default function DocumentVersions() {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const { toast } = useToast();

  const [document, setDocument] = useState<DMSDocument | null>(null);
  const [versions, setVersions] = useState<DocumentVersion[]>([]);
  const [loading, setLoading] = useState(true);

  // Upload new version state
  const [showUploadDialog, setShowUploadDialog] = useState(false);
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [changeNotes, setChangeNotes] = useState('');
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);

  const fetchData = async () => {
    if (!id) return;

    try {
      const [doc, vers] = await Promise.all([
        documentApi.get(id),
        documentApi.getVersions(id),
      ]);
      setDocument(doc);
      setVersions(vers);
    } catch (error) {
      console.error('Failed to fetch document:', error);
      toast({
        title: 'Error',
        description: 'Failed to load document versions',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [id]);

  const onDrop = (acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      setUploadFile(acceptedFiles[0]);
    }
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    multiple: false,
  });

  const handleUploadVersion = async () => {
    if (!id || !uploadFile) return;

    setUploading(true);
    setUploadProgress(0);

    try {
      // Simulate progress
      const progressInterval = setInterval(() => {
        setUploadProgress((prev) => Math.min(prev + 10, 90));
      }, 200);

      await documentApi.uploadVersion(id, uploadFile, changeNotes || undefined);

      clearInterval(progressInterval);
      setUploadProgress(100);

      toast({
        title: 'Success',
        description: 'New version uploaded successfully',
      });

      setShowUploadDialog(false);
      setUploadFile(null);
      setChangeNotes('');
      fetchData();
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to upload new version',
        variant: 'destructive',
      });
    } finally {
      setUploading(false);
      setUploadProgress(0);
    }
  };

  const handleDownloadVersion = async (version: DocumentVersion) => {
    if (!id) return;

    try {
      const blob = await documentApi.download(id, version.version_number);
      const url = window.URL.createObjectURL(blob);
      const a = window.document.createElement('a');
      a.href = url;
      a.download = version.file_name;
      window.document.body?.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      window.document.body?.removeChild(a);

      toast({
        title: 'Download Started',
        description: `Downloading version ${version.version_number}`,
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to download version',
        variant: 'destructive',
      });
    }
  };

  const getDocIcon = () => {
    const ext = document?.file_extension?.toLowerCase() || '';
    if (['jpg', 'jpeg', 'png', 'gif', 'svg', 'webp'].includes(ext)) {
      return <FileImage className="h-12 w-12 text-green-500" />;
    }
    if (['xlsx', 'xls', 'csv'].includes(ext)) {
      return <FileSpreadsheet className="h-12 w-12 text-emerald-500" />;
    }
    if (ext === 'pdf') {
      return <FileText className="h-12 w-12 text-red-500" />;
    }
    return <File className="h-12 w-12 text-gray-500" />;
  };

  if (loading) {
    return (
      <div className="space-y-6 p-6">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-96" />
      </div>
    );
  }

  if (!document) {
    return (
      <div className="p-6 text-center">
        <FileText className="h-16 w-16 mx-auto text-muted-foreground mb-4" />
        <h2 className="text-xl font-semibold mb-2">Document Not Found</h2>
        <Button onClick={() => navigate('/admin/dms')}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to DMS
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-start gap-4">
          <Button variant="ghost" size="icon" onClick={() => navigate(-1)}>
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div className="flex items-center gap-4">
            {getDocIcon()}
            <div>
              <h1 className="text-2xl font-bold">{document.name}</h1>
              <p className="text-muted-foreground">
                Version History • {versions.length} version{versions.length !== 1 ? 's' : ''}
              </p>
            </div>
          </div>
        </div>
        <Button onClick={() => setShowUploadDialog(true)}>
          <Upload className="h-4 w-4 mr-2" />
          Upload New Version
        </Button>
      </div>

      {/* Current Version Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Check className="h-5 w-5 text-green-500" />
            Current Version
          </CardTitle>
          <CardDescription>
            This is the active version of the document
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <p className="text-sm text-muted-foreground">Version</p>
              <p className="font-medium text-lg">v{document.current_version}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">File Name</p>
              <p className="font-medium truncate">{document.file_name}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">File Size</p>
              <p className="font-medium">{formatFileSize(document.file_size)}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Last Updated</p>
              <p className="font-medium">
                {new Date(document.updated_at || document.created_at).toLocaleString()}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Version History Table */}
      <Card>
        <CardHeader>
          <CardTitle>Version History</CardTitle>
          <CardDescription>
            All versions of this document
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Version</TableHead>
                <TableHead>File Name</TableHead>
                <TableHead>Size</TableHead>
                <TableHead>Change Notes</TableHead>
                <TableHead>Uploaded</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {versions.map((version) => (
                <TableRow key={version.id}>
                  <TableCell>
                    <Badge
                      variant={version.is_current ? 'default' : 'outline'}
                      className="font-mono"
                    >
                      v{version.version_number}
                    </Badge>
                  </TableCell>
                  <TableCell className="font-medium">
                    <div className="flex items-center gap-2">
                      <File className="h-4 w-4 text-muted-foreground" />
                      <span className="truncate max-w-[200px]">
                        {version.file_name}
                      </span>
                    </div>
                  </TableCell>
                  <TableCell>{formatFileSize(version.file_size)}</TableCell>
                  <TableCell>
                    <span className="text-sm text-muted-foreground line-clamp-1">
                      {version.change_notes || '-'}
                    </span>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-1 text-sm text-muted-foreground">
                      <Clock className="h-3 w-3" />
                      {new Date(version.created_at).toLocaleString()}
                    </div>
                  </TableCell>
                  <TableCell>
                    {version.is_current ? (
                      <Badge variant="default" className="bg-green-500">
                        <Check className="h-3 w-3 mr-1" />
                        Current
                      </Badge>
                    ) : (
                      <Badge variant="secondary">Previous</Badge>
                    )}
                  </TableCell>
                  <TableCell className="text-right">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleDownloadVersion(version)}
                    >
                      <Download className="h-4 w-4 mr-1" />
                      Download
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>

          {versions.length === 0 && (
            <div className="text-center py-8 text-muted-foreground">
              No version history available
            </div>
          )}
        </CardContent>
      </Card>

      {/* Upload New Version Dialog */}
      <Dialog open={showUploadDialog} onOpenChange={setShowUploadDialog}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Upload New Version</DialogTitle>
            <DialogDescription>
              Upload a new version of "{document.name}". This will become the
              current version.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            {/* Dropzone */}
            <div
              {...getRootProps()}
              className={`border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors
                ${isDragActive ? 'border-primary bg-primary/5' : 'border-muted-foreground/25 hover:border-primary/50'}
                ${uploadFile ? 'border-green-500 bg-green-50' : ''}
              `}
            >
              <input {...getInputProps()} />
              {uploadFile ? (
                <div className="flex items-center justify-center gap-3">
                  <File className="h-8 w-8 text-green-500" />
                  <div className="text-left">
                    <p className="font-medium">{uploadFile.name}</p>
                    <p className="text-sm text-muted-foreground">
                      {formatFileSize(uploadFile.size)}
                    </p>
                  </div>
                </div>
              ) : (
                <>
                  <Upload className="h-8 w-8 mx-auto text-muted-foreground mb-2" />
                  <p className="text-sm font-medium">
                    {isDragActive ? 'Drop file here' : 'Click or drag file to upload'}
                  </p>
                  <p className="text-xs text-muted-foreground mt-1">
                    Current: {document.file_name}
                  </p>
                </>
              )}
            </div>

            {/* Change Notes */}
            <div>
              <Label>Change Notes (Optional)</Label>
              <Textarea
                placeholder="Describe what changed in this version..."
                value={changeNotes}
                onChange={(e) => setChangeNotes(e.target.value)}
                rows={3}
              />
            </div>

            {/* Upload Progress */}
            {uploading && (
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span>Uploading...</span>
                  <span>{uploadProgress}%</span>
                </div>
                <Progress value={uploadProgress} />
              </div>
            )}
          </div>

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setShowUploadDialog(false);
                setUploadFile(null);
                setChangeNotes('');
              }}
              disabled={uploading}
            >
              Cancel
            </Button>
            <Button
              onClick={handleUploadVersion}
              disabled={!uploadFile || uploading}
            >
              {uploading ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Uploading...
                </>
              ) : (
                <>
                  <Upload className="h-4 w-4 mr-2" />
                  Upload Version
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
