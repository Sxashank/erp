/**
 * Document Upload Page
 * Upload new documents with metadata
 */

import { useState, useCallback, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useDropzone } from 'react-dropzone';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import {
  Upload,
  File,
  FileImage,
  FileText,
  FileSpreadsheet,
  X,
  CheckCircle,
  AlertCircle,
  Loader2,
  FolderOpen,
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { PageHeader } from '@/components/common/PageHeader';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { useToast } from '@/hooks/use-toast';
import { documentApi, folderApi } from '@/services/dmsApi';
import type { DMSFolder, DocumentCreate } from '@/types/dms';
import { formatFileSize, DOCUMENT_TYPES, ACCESS_LEVELS } from '@/types/dms';

const uploadSchema = z.object({
  name: z.string().optional(),
  description: z.string().optional(),
  document_type: z.string().optional(),
  document_subtype: z.string().optional(),
  access_level: z.string().default('organization'),
  keywords: z.string().optional(),
  expiry_date: z.string().optional(),
  entity_type: z.string().optional(),
  entity_id: z.string().optional(),
});

type UploadFormData = z.infer<typeof uploadSchema>;

interface FileUploadStatus {
  file: File;
  status: 'pending' | 'uploading' | 'success' | 'error';
  progress: number;
  error?: string;
  documentId?: string;
}

export default function DocumentUpload() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { toast } = useToast();

  const folderId = searchParams.get('folder') || undefined;

  const [files, setFiles] = useState<FileUploadStatus[]>([]);
  const [folders, setFolders] = useState<DMSFolder[]>([]);
  const [selectedFolder, setSelectedFolder] = useState<string | undefined>(folderId);
  const [uploading, setUploading] = useState(false);

  const form = useForm<UploadFormData>({
    resolver: zodResolver(uploadSchema) as any,
    defaultValues: {
      access_level: 'organization',
    },
  });

  useEffect(() => {
    // Fetch folder tree for selection
    const fetchFolders = async () => {
      try {
        const tree = await folderApi.getTree({ max_depth: 5 });
        // Flatten tree for simple select
        const flattenTree = (nodes: any[], level = 0): DMSFolder[] => {
          let result: DMSFolder[] = [];
          for (const node of nodes) {
            result.push({ ...node, level } as DMSFolder);
            if (node.children?.length) {
              result = result.concat(flattenTree(node.children, level + 1));
            }
          }
          return result;
        };
        setFolders(flattenTree(tree));
      } catch (error) {
        console.error('Failed to fetch folders:', error);
      }
    };
    fetchFolders();
  }, []);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const newFiles = acceptedFiles.map((file) => ({
      file,
      status: 'pending' as const,
      progress: 0,
    }));
    setFiles((prev) => [...prev, ...newFiles]);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    multiple: true,
  });

  const removeFile = (index: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const getFileIcon = (file: File) => {
    if (file.type.startsWith('image/')) {
      return <FileImage className="h-8 w-8 text-green-500" />;
    }
    if (file.type === 'application/pdf') {
      return <FileText className="h-8 w-8 text-red-500" />;
    }
    if (file.type.includes('spreadsheet') || file.name.endsWith('.xlsx') || file.name.endsWith('.xls')) {
      return <FileSpreadsheet className="h-8 w-8 text-emerald-500" />;
    }
    return <File className="h-8 w-8 text-gray-500" />;
  };

  const handleUpload = async (data: UploadFormData) => {
    if (files.length === 0) {
      toast({
        title: 'No files selected',
        description: 'Please select at least one file to upload',
        variant: 'destructive',
      });
      return;
    }

    setUploading(true);

    const metadata: DocumentCreate = {
      folder_id: selectedFolder,
      name: data.name || undefined,
      description: data.description || undefined,
      document_type: data.document_type || undefined,
      document_subtype: data.document_subtype || undefined,
      access_level: data.access_level,
      keywords: data.keywords ? data.keywords.split(',').map((k) => k.trim()).filter(Boolean) : undefined,
      expiry_date: data.expiry_date || undefined,
      entity_type: data.entity_type || undefined,
      entity_id: data.entity_id || undefined,
    };

    // Upload files sequentially
    for (let i = 0; i < files.length; i++) {
      const fileStatus = files[i];
      if (fileStatus.status !== 'pending') continue;

      // Update status to uploading
      setFiles((prev) =>
        prev.map((f, idx) =>
          idx === i ? { ...f, status: 'uploading' as const, progress: 0 } : f
        )
      );

      try {
        // Simulate progress (real progress would need XMLHttpRequest)
        const progressInterval = setInterval(() => {
          setFiles((prev) =>
            prev.map((f, idx) =>
              idx === i && f.status === 'uploading'
                ? { ...f, progress: Math.min(f.progress + 10, 90) }
                : f
            )
          );
        }, 200);

        const document = await documentApi.upload(fileStatus.file, {
          ...metadata,
          name: metadata.name || fileStatus.file.name,
        });

        clearInterval(progressInterval);

        setFiles((prev) =>
          prev.map((f, idx) =>
            idx === i
              ? { ...f, status: 'success' as const, progress: 100, documentId: document.id }
              : f
          )
        );
      } catch (error: any) {
        setFiles((prev) =>
          prev.map((f, idx) =>
            idx === i
              ? {
                  ...f,
                  status: 'error' as const,
                  progress: 0,
                  error: error.message || 'Upload failed',
                }
              : f
          )
        );
      }
    }

    setUploading(false);

    const successCount = files.filter((f) => f.status === 'success').length;
    const errorCount = files.filter((f) => f.status === 'error').length;

    if (successCount > 0) {
      toast({
        title: 'Upload Complete',
        description: `${successCount} file(s) uploaded successfully${
          errorCount > 0 ? `, ${errorCount} failed` : ''
        }`,
      });
    }
  };

  const allDone = files.length > 0 && files.every((f) => f.status === 'success' || f.status === 'error');

  return (
    <div className="space-y-6 p-6">
      <PageHeader
        title="Upload Documents"
        subtitle="Upload new documents to your document management system"
        breadcrumbs={[
          { label: 'DMS', to: '/admin/dms' },
          { label: 'Upload' },
        ]}
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Upload Area */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Select Files</CardTitle>
            <CardDescription>
              Drag and drop files or click to browse
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div
              {...getRootProps()}
              className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors
                ${isDragActive ? 'border-primary bg-primary/5' : 'border-muted-foreground/25 hover:border-primary/50'}
              `}
            >
              <input {...getInputProps()} />
              <Upload className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
              {isDragActive ? (
                <p className="text-lg font-medium">Drop files here...</p>
              ) : (
                <>
                  <p className="text-lg font-medium">Drag & drop files here</p>
                  <p className="text-muted-foreground mt-2">
                    or click to browse from your computer
                  </p>
                </>
              )}
            </div>

            {/* File List */}
            {files.length > 0 && (
              <div className="mt-6 space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="font-medium">Selected Files ({files.length})</h3>
                  {!uploading && (
                    <Button variant="ghost" size="sm" onClick={() => setFiles([])}>
                      Clear All
                    </Button>
                  )}
                </div>
                {files.map((fileStatus, index) => (
                  <div
                    key={index}
                    className="flex items-center gap-3 p-3 border rounded-lg"
                  >
                    {getFileIcon(fileStatus.file)}
                    <div className="flex-1 min-w-0">
                      <p className="font-medium truncate">{fileStatus.file.name}</p>
                      <p className="text-xs text-muted-foreground">
                        {formatFileSize(fileStatus.file.size)}
                      </p>
                      {fileStatus.status === 'uploading' && (
                        <Progress value={fileStatus.progress} className="h-1 mt-2" />
                      )}
                      {fileStatus.status === 'error' && (
                        <p className="text-xs text-red-500 mt-1">{fileStatus.error}</p>
                      )}
                    </div>
                    {fileStatus.status === 'pending' && (
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => removeFile(index)}
                        disabled={uploading}
                      >
                        <X className="h-4 w-4" />
                      </Button>
                    )}
                    {fileStatus.status === 'uploading' && (
                      <Loader2 className="h-5 w-5 animate-spin text-primary" />
                    )}
                    {fileStatus.status === 'success' && (
                      <CheckCircle className="h-5 w-5 text-green-500" />
                    )}
                    {fileStatus.status === 'error' && (
                      <AlertCircle className="h-5 w-5 text-red-500" />
                    )}
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Metadata Form */}
        <Card>
          <CardHeader>
            <CardTitle>Document Details</CardTitle>
            <CardDescription>
              Add metadata to your documents (optional)
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Form {...form}>
              <form onSubmit={form.handleSubmit(handleUpload as any)} className="space-y-4">
                {/* Folder Selection */}
                <div className="space-y-2">
                  <Label>Destination Folder</Label>
                  <Select
                    value={selectedFolder || 'root'}
                    onValueChange={(value) =>
                      setSelectedFolder(value === 'root' ? undefined : value)
                    }
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select folder" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="root">
                        <div className="flex items-center gap-2">
                          <FolderOpen className="h-4 w-4" />
                          Root
                        </div>
                      </SelectItem>
                      {folders.map((folder) => (
                        <SelectItem key={folder.id} value={folder.id}>
                          <div className="flex items-center gap-2">
                            <span style={{ paddingLeft: folder.level * 16 }}>
                              {folder.name}
                            </span>
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <FormField
                  control={form.control}
                  name="name"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Document Name</FormLabel>
                      <FormControl>
                        <Input placeholder="Optional custom name" {...field} />
                      </FormControl>
                      <FormDescription>
                        Leave empty to use filename
                      </FormDescription>
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="description"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Description</FormLabel>
                      <FormControl>
                        <Textarea
                          placeholder="Optional description"
                          rows={2}
                          {...field}
                        />
                      </FormControl>
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="document_type"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Document Type</FormLabel>
                      <Select
                        value={field.value}
                        onValueChange={field.onChange}
                      >
                        <FormControl>
                          <SelectTrigger>
                            <SelectValue placeholder="Select type" />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          {DOCUMENT_TYPES.map((type) => (
                            <SelectItem key={type.value} value={type.value}>
                              {type.label}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="access_level"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Access Level</FormLabel>
                      <Select
                        value={field.value}
                        onValueChange={field.onChange}
                      >
                        <FormControl>
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          {ACCESS_LEVELS.map((level) => (
                            <SelectItem key={level.value} value={level.value}>
                              {level.label}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="keywords"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Keywords</FormLabel>
                      <FormControl>
                        <Input
                          placeholder="keyword1, keyword2, ..."
                          {...field}
                        />
                      </FormControl>
                      <FormDescription>
                        Comma-separated keywords for search
                      </FormDescription>
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="expiry_date"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Expiry Date</FormLabel>
                      <FormControl>
                        <Input type="date" {...field} />
                      </FormControl>
                      <FormDescription>
                        Optional document expiry date
                      </FormDescription>
                    </FormItem>
                  )}
                />

                <div className="pt-4">
                  {allDone ? (
                    <div className="space-y-3">
                      <Button
                        type="button"
                        className="w-full"
                        onClick={() => navigate('/admin/dms')}
                      >
                        Go to Dashboard
                      </Button>
                      <Button
                        type="button"
                        variant="outline"
                        className="w-full"
                        onClick={() => {
                          setFiles([]);
                          form.reset();
                        }}
                      >
                        Upload More
                      </Button>
                    </div>
                  ) : (
                    <Button
                      type="submit"
                      className="w-full"
                      disabled={files.length === 0 || uploading}
                    >
                      {uploading ? (
                        <>
                          <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                          Uploading...
                        </>
                      ) : (
                        <>
                          <Upload className="h-4 w-4 mr-2" />
                          Upload {files.length} File{files.length !== 1 ? 's' : ''}
                        </>
                      )}
                    </Button>
                  )}
                </div>
              </form>
            </Form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
