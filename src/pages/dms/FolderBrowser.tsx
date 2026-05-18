/**
 * Folder Browser Page
 * Browse and manage folders and documents in a hierarchical structure
 */

import {
  Folder,
  FolderPlus,
  FileText,
  ChevronRight,
  Home,
  MoreVertical,
  Pencil,
  Trash2,
  Upload,
  ArrowLeft,
  Grid,
  List,
  RefreshCw,
  File,
  FileImage,
  FileSpreadsheet,
} from 'lucide-react';
import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';

import { PageHeader } from '@/components/common/PageHeader';
import { Badge } from '@/components/ui/badge';
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from '@/components/ui/breadcrumb';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Skeleton } from '@/components/ui/skeleton';
import { Textarea } from '@/components/ui/textarea';
import { useToast } from '@/hooks/use-toast';
import { folderApi, documentApi } from '@/services/dmsApi';
import type { DMSFolder, DMSDocument, FolderCreate } from '@/types/dms';
import { formatFileSize, ACCESS_LEVELS } from '@/types/dms';

import { logger } from "@/lib/logger";
export default function FolderBrowser() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const { toast } = useToast();

  const currentFolderId = searchParams.get('folder') || undefined;

  const [folders, setFolders] = useState<DMSFolder[]>([]);
  const [documents, setDocuments] = useState<DMSDocument[]>([]);
  const [currentFolder, setCurrentFolder] = useState<DMSFolder | null>(null);
  const [breadcrumbs, setBreadcrumbs] = useState<DMSFolder[]>([]);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');

  // Create folder dialog state
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [newFolderData, setNewFolderData] = useState<FolderCreate>({
    name: '',
    description: '',
    access_level: 'organization',
    color: '#3b82f6',
  });
  const [creating, setCreating] = useState(false);

  // Edit folder dialog state
  const [editingFolder, setEditingFolder] = useState<DMSFolder | null>(null);
  const [showEditDialog, setShowEditDialog] = useState(false);

  // Delete confirmation
  const [deletingFolder, setDeletingFolder] = useState<DMSFolder | null>(null);
  const [deleting, setDeleting] = useState(false);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [foldersData, docsResponse] = await Promise.all([
        folderApi.list({ parent_id: currentFolderId }),
        currentFolderId
          ? folderApi.getDocuments(currentFolderId, { limit: 50 })
          : documentApi.list({ folder_id: undefined, limit: 50 }),
      ]);

      setFolders(foldersData);
      setDocuments(docsResponse.items || []);

      // Fetch current folder details if we're in a subfolder
      if (currentFolderId) {
        const folder = await folderApi.get(currentFolderId);
        setCurrentFolder(folder);

        // Build breadcrumbs from path
        const pathParts = folder.path.split('/').filter(Boolean);
        // For now, just show current folder in breadcrumb
        setBreadcrumbs([folder]);
      } else {
        setCurrentFolder(null);
        setBreadcrumbs([]);
      }
    } catch (error) {
      logger.error('Failed to fetch folder data:', error);
      toast({
        title: 'Error',
        description: 'Failed to load folder contents',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [currentFolderId]);

  const handleCreateFolder = async () => {
    if (!newFolderData.name.trim()) {
      toast({
        title: 'Validation Error',
        description: 'Folder name is required',
        variant: 'destructive',
      });
      return;
    }

    setCreating(true);
    try {
      await folderApi.create({
        ...newFolderData,
        parent_id: currentFolderId,
      });
      toast({
        title: 'Success',
        description: 'Folder created successfully',
      });
      setShowCreateDialog(false);
      setNewFolderData({
        name: '',
        description: '',
        access_level: 'organization',
        color: '#3b82f6',
      });
      fetchData();
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to create folder',
        variant: 'destructive',
      });
    } finally {
      setCreating(false);
    }
  };

  const handleEditFolder = async () => {
    if (!editingFolder) return;

    try {
      await folderApi.update(editingFolder.id, {
        name: editingFolder.name,
        description: editingFolder.description,
        color: editingFolder.color,
        access_level: editingFolder.access_level,
      });
      toast({
        title: 'Success',
        description: 'Folder updated successfully',
      });
      setShowEditDialog(false);
      setEditingFolder(null);
      fetchData();
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to update folder',
        variant: 'destructive',
      });
    }
  };

  const handleDeleteFolder = async () => {
    if (!deletingFolder) return;

    setDeleting(true);
    try {
      await folderApi.delete(deletingFolder.id, true);
      toast({
        title: 'Success',
        description: 'Folder deleted successfully',
      });
      setDeletingFolder(null);
      fetchData();
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to delete folder',
        variant: 'destructive',
      });
    } finally {
      setDeleting(false);
    }
  };

  const navigateToFolder = (folderId?: string) => {
    if (folderId) {
      setSearchParams({ folder: folderId });
    } else {
      setSearchParams({});
    }
  };

  const getDocIcon = (doc: DMSDocument) => {
    const ext = doc.file_extension?.toLowerCase() || '';
    if (['jpg', 'jpeg', 'png', 'gif', 'svg', 'webp'].includes(ext)) {
      return <FileImage className="h-8 w-8 text-green-500" />;
    }
    if (['xlsx', 'xls', 'csv'].includes(ext)) {
      return <FileSpreadsheet className="h-8 w-8 text-emerald-500" />;
    }
    if (ext === 'pdf') {
      return <FileText className="h-8 w-8 text-red-500" />;
    }
    return <File className="h-8 w-8 text-gray-500" />;
  };

  if (loading) {
    return (
      <div className="space-y-6 p-6">
        <Skeleton className="h-8 w-64" />
        <div className="grid grid-cols-2 gap-4 md:grid-cols-4 lg:grid-cols-6">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <Skeleton key={i} className="h-32" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6">
      <PageHeader
        title="Folder Browser"
        subtitle={breadcrumbs.length === 0 ? 'Root' : breadcrumbs.map((f) => f.name).join(' / ')}
        actions={
          <div className="flex gap-2">
            <Button variant="outline" size="icon" onClick={() => setViewMode('grid')}>
              <Grid className={`h-4 w-4 ${viewMode === 'grid' ? 'text-primary' : ''}`} />
            </Button>
            <Button variant="outline" size="icon" onClick={() => setViewMode('list')}>
              <List className={`h-4 w-4 ${viewMode === 'list' ? 'text-primary' : ''}`} />
            </Button>
            <Button variant="outline" onClick={fetchData}>
              <RefreshCw className="mr-2 h-4 w-4" />
              Refresh
            </Button>
            <Button variant="outline" onClick={() => setShowCreateDialog(true)}>
              <FolderPlus className="mr-2 h-4 w-4" />
              New Folder
            </Button>
            <Button
              onClick={() =>
                navigate(
                  currentFolderId
                    ? `/admin/dms/upload?folder=${currentFolderId}`
                    : '/admin/dms/upload',
                )
              }
            >
              <Upload className="mr-2 h-4 w-4" />
              Upload
            </Button>
          </div>
        }
      />

      {/* Folder path breadcrumb — richer than PageHeader's text-only path, clickable per segment */}
      <Breadcrumb>
        <BreadcrumbList>
          <BreadcrumbItem>
            <BreadcrumbLink
              className="flex cursor-pointer items-center gap-1"
              onClick={() => navigateToFolder()}
            >
              <Home className="h-4 w-4" />
              Root
            </BreadcrumbLink>
          </BreadcrumbItem>
          {breadcrumbs.map((folder, index) => (
            <BreadcrumbItem key={folder.id}>
              <BreadcrumbSeparator>
                <ChevronRight className="h-4 w-4" />
              </BreadcrumbSeparator>
              {index === breadcrumbs.length - 1 ? (
                <BreadcrumbPage>{folder.name}</BreadcrumbPage>
              ) : (
                <BreadcrumbLink
                  className="cursor-pointer"
                  onClick={() => navigateToFolder(folder.id)}
                >
                  {folder.name}
                </BreadcrumbLink>
              )}
            </BreadcrumbItem>
          ))}
        </BreadcrumbList>
      </Breadcrumb>

      {/* Back button for subfolders */}
      {currentFolderId && (
        <Button
          variant="ghost"
          onClick={() => navigateToFolder(currentFolder?.parent_id || undefined)}
        >
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back
        </Button>
      )}

      {/* Content */}
      {folders.length === 0 && documents.length === 0 ? (
        <Card className="p-12">
          <div className="text-center">
            <Folder className="mx-auto mb-4 h-16 w-16 text-muted-foreground" />
            <h3 className="mb-2 text-lg font-semibold">This folder is empty</h3>
            <p className="mb-4 text-muted-foreground">
              Create a new folder or upload documents to get started
            </p>
            <div className="flex justify-center gap-2">
              <Button variant="outline" onClick={() => setShowCreateDialog(true)}>
                <FolderPlus className="mr-2 h-4 w-4" />
                New Folder
              </Button>
              <Button
                onClick={() =>
                  navigate(
                    currentFolderId
                      ? `/admin/dms/upload?folder=${currentFolderId}`
                      : '/admin/dms/upload',
                  )
                }
              >
                <Upload className="mr-2 h-4 w-4" />
                Upload Document
              </Button>
            </div>
          </div>
        </Card>
      ) : viewMode === 'grid' ? (
        <div className="space-y-6">
          {/* Folders Grid */}
          {folders.length > 0 && (
            <div>
              <h3 className="mb-3 text-sm font-medium text-muted-foreground">Folders</h3>
              <div className="grid grid-cols-2 gap-4 md:grid-cols-4 lg:grid-cols-6">
                {folders.map((folder) => (
                  <Card
                    key={folder.id}
                    className="group cursor-pointer transition-shadow hover:shadow-md"
                    onClick={() => navigateToFolder(folder.id)}
                  >
                    <CardContent className="relative p-4 text-center">
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild onClick={(e) => e.stopPropagation()}>
                          <Button
                            variant="ghost"
                            size="icon"
                            className="absolute right-1 top-1 h-6 w-6 opacity-0 transition-opacity group-hover:opacity-100"
                          >
                            <MoreVertical className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent>
                          <DropdownMenuItem
                            onClick={(e) => {
                              e.stopPropagation();
                              setEditingFolder(folder);
                              setShowEditDialog(true);
                            }}
                          >
                            <Pencil className="mr-2 h-4 w-4" />
                            Edit
                          </DropdownMenuItem>
                          <DropdownMenuSeparator />
                          <DropdownMenuItem
                            className="text-red-600"
                            onClick={(e) => {
                              e.stopPropagation();
                              setDeletingFolder(folder);
                            }}
                          >
                            <Trash2 className="mr-2 h-4 w-4" />
                            Delete
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                      <Folder
                        className="mx-auto mb-2 h-12 w-12"
                        style={{ color: folder.color || '#3b82f6' }}
                      />
                      <p className="truncate font-medium">{folder.name}</p>
                      <p className="text-xs text-muted-foreground">
                        {folder.document_count} documents
                      </p>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          )}

          {/* Documents Grid */}
          {documents.length > 0 && (
            <div>
              <h3 className="mb-3 text-sm font-medium text-muted-foreground">Documents</h3>
              <div className="grid grid-cols-2 gap-4 md:grid-cols-4 lg:grid-cols-6">
                {documents.map((doc) => (
                  <Card
                    key={doc.id}
                    className="cursor-pointer transition-shadow hover:shadow-md"
                    onClick={() => navigate(`/admin/dms/documents/${doc.id}`)}
                  >
                    <CardContent className="p-4 text-center">
                      {getDocIcon(doc)}
                      <p className="mt-2 truncate font-medium">{doc.name}</p>
                      <p className="text-xs text-muted-foreground">
                        {formatFileSize(doc.file_size)}
                      </p>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          )}
        </div>
      ) : (
        <div className="space-y-4">
          {/* Folders List */}
          {folders.map((folder) => (
            <div
              key={folder.id}
              className="flex cursor-pointer items-center gap-4 rounded-lg border p-4 transition-colors hover:bg-accent"
              onClick={() => navigateToFolder(folder.id)}
            >
              <Folder className="h-8 w-8" style={{ color: folder.color || '#3b82f6' }} />
              <div className="flex-1">
                <p className="font-medium">{folder.name}</p>
                <p className="text-sm text-muted-foreground">
                  {folder.document_count} documents • {folder.path}
                </p>
              </div>
              <Badge variant="outline">{folder.access_level}</Badge>
              <DropdownMenu>
                <DropdownMenuTrigger asChild onClick={(e) => e.stopPropagation()}>
                  <Button variant="ghost" size="icon">
                    <MoreVertical className="h-4 w-4" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent>
                  <DropdownMenuItem
                    onClick={(e) => {
                      e.stopPropagation();
                      setEditingFolder(folder);
                      setShowEditDialog(true);
                    }}
                  >
                    <Pencil className="mr-2 h-4 w-4" />
                    Edit
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem
                    className="text-red-600"
                    onClick={(e) => {
                      e.stopPropagation();
                      setDeletingFolder(folder);
                    }}
                  >
                    <Trash2 className="mr-2 h-4 w-4" />
                    Delete
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          ))}

          {/* Documents List */}
          {documents.map((doc) => (
            <div
              key={doc.id}
              className="flex cursor-pointer items-center gap-4 rounded-lg border p-4 transition-colors hover:bg-accent"
              onClick={() => navigate(`/admin/dms/documents/${doc.id}`)}
            >
              {getDocIcon(doc)}
              <div className="flex-1">
                <p className="font-medium">{doc.name}</p>
                <p className="text-sm text-muted-foreground">
                  {formatFileSize(doc.file_size)} • {doc.file_extension?.toUpperCase()} • v
                  {doc.current_version}
                </p>
              </div>
              <Badge variant="outline">{doc.status}</Badge>
            </div>
          ))}
        </div>
      )}

      {/* Create Folder Dialog */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create New Folder</DialogTitle>
            <DialogDescription>Create a new folder to organize your documents</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>Folder Name *</Label>
              <Input
                value={newFolderData.name}
                onChange={(e) => setNewFolderData({ ...newFolderData, name: e.target.value })}
                placeholder="Enter folder name"
              />
            </div>
            <div>
              <Label>Description</Label>
              <Textarea
                value={newFolderData.description || ''}
                onChange={(e) =>
                  setNewFolderData({ ...newFolderData, description: e.target.value })
                }
                placeholder="Optional description"
                rows={3}
              />
            </div>
            <div>
              <Label>Access Level</Label>
              <Select
                value={newFolderData.access_level}
                onValueChange={(value) =>
                  setNewFolderData({ ...newFolderData, access_level: value })
                }
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {ACCESS_LEVELS.map((level) => (
                    <SelectItem key={level.value} value={level.value}>
                      {level.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Color</Label>
              <Input
                type="color"
                value={newFolderData.color || '#3b82f6'}
                onChange={(e) => setNewFolderData({ ...newFolderData, color: e.target.value })}
                className="h-10 w-20"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCreateDialog(false)}>
              Cancel
            </Button>
            <Button onClick={handleCreateFolder} disabled={creating}>
              {creating ? 'Creating...' : 'Create Folder'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Edit Folder Dialog */}
      <Dialog open={showEditDialog} onOpenChange={setShowEditDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Edit Folder</DialogTitle>
          </DialogHeader>
          {editingFolder && (
            <div className="space-y-4">
              <div>
                <Label>Folder Name</Label>
                <Input
                  value={editingFolder.name}
                  onChange={(e) => setEditingFolder({ ...editingFolder, name: e.target.value })}
                />
              </div>
              <div>
                <Label>Description</Label>
                <Textarea
                  value={editingFolder.description || ''}
                  onChange={(e) =>
                    setEditingFolder({ ...editingFolder, description: e.target.value })
                  }
                  rows={3}
                />
              </div>
              <div>
                <Label>Color</Label>
                <Input
                  type="color"
                  value={editingFolder.color || '#3b82f6'}
                  onChange={(e) => setEditingFolder({ ...editingFolder, color: e.target.value })}
                  className="h-10 w-20"
                />
              </div>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowEditDialog(false)}>
              Cancel
            </Button>
            <Button onClick={handleEditFolder}>Save Changes</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={!!deletingFolder} onOpenChange={() => setDeletingFolder(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Folder</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete "{deletingFolder?.name}"? This will also delete all
              documents and subfolders inside it. This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeletingFolder(null)}>
              Cancel
            </Button>
            <Button variant="destructive" onClick={handleDeleteFolder} disabled={deleting}>
              {deleting ? 'Deleting...' : 'Delete'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
