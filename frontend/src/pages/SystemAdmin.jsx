import React, { useState, useEffect } from 'react';
import api from '../lib/api';
import { toast } from 'sonner';
import {
  Database,
  HardDrive,
  Download,
  Upload,
  Trash2,
  AlertTriangle,
  RefreshCw,
  Clock,
  CheckCircle,
  XCircle,
  FileArchive,
  Calendar,
  Server
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogDescription
} from '../components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue
} from '../components/ui/select';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle
} from '../components/ui/card';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle
} from '../components/ui/alert-dialog';

export default function SystemAdmin() {
  const [systemInfo, setSystemInfo] = useState(null);
  const [backups, setBackups] = useState([]);
  const [loading, setLoading] = useState(true);
  const [backupLoading, setBackupLoading] = useState(false);
  const [resetPreview, setResetPreview] = useState(null);
  const [restorePreview, setRestorePreview] = useState(null);
  
  // Modal states
  const [showResetModal, setShowResetModal] = useState(false);
  const [showBackupModal, setShowBackupModal] = useState(false);
  const [showRestoreModal, setShowRestoreModal] = useState(false);
  const [selectedBackup, setSelectedBackup] = useState(null);
  
  // Form states
  const [resetType, setResetType] = useState('transactional');
  const [resetConfirmation, setResetConfirmation] = useState('');
  const [restoreConfirmation, setRestoreConfirmation] = useState('');
  const [backupName, setBackupName] = useState('');
  const [backupDescription, setBackupDescription] = useState('');

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [infoRes, backupsRes] = await Promise.all([
        api.get('/admin/system-info'),
        api.get('/admin/backups')
      ]);
      setSystemInfo(infoRes.data);
      setBackups(backupsRes.data);
    } catch (error) {
      toast.error('Failed to fetch system information');
    } finally {
      setLoading(false);
    }
  };

  const fetchResetPreview = async (type) => {
    try {
      const response = await api.get('/admin/data-reset/preview', {
        params: { reset_type: type }
      });
      setResetPreview(response.data);
    } catch (error) {
      toast.error('Failed to fetch reset preview');
    }
  };

  const handleResetTypeChange = (type) => {
    setResetType(type);
    fetchResetPreview(type);
  };

  const handleDataReset = async () => {
    if (resetConfirmation !== 'RESET') {
      toast.error('Please type RESET to confirm');
      return;
    }

    try {
      const response = await api.post('/admin/data-reset', {
        reset_type: resetType,
        confirmation_code: resetConfirmation,
        keep_users: true,
        keep_company_settings: true
      });
      toast.success(response.data.message);
      setShowResetModal(false);
      setResetConfirmation('');
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Reset failed');
    }
  };

  const handleCreateBackup = async () => {
    try {
      setBackupLoading(true);
      await api.post('/admin/backups', {
        name: backupName || undefined,
        description: backupDescription || undefined,
        backup_type: 'full'
      });
      toast.success('Backup created successfully');
      setShowBackupModal(false);
      setBackupName('');
      setBackupDescription('');
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Backup failed');
    } finally {
      setBackupLoading(false);
    }
  };

  const fetchRestorePreview = async (backupId) => {
    try {
      const response = await api.get(`/admin/restore/preview/${backupId}`);
      setRestorePreview(response.data);
    } catch (error) {
      toast.error('Failed to fetch restore preview');
    }
  };

  const handleRestore = async () => {
    if (restoreConfirmation !== 'RESTORE') {
      toast.error('Please type RESTORE to confirm');
      return;
    }

    try {
      const response = await api.post('/admin/restore', {
        backup_id: selectedBackup.id,
        confirmation_code: restoreConfirmation
      });
      toast.success(response.data.message);
      setShowRestoreModal(false);
      setRestoreConfirmation('');
      setSelectedBackup(null);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Restore failed');
    }
  };

  const handleDeleteBackup = async (backupId) => {
    if (!window.confirm('Are you sure you want to delete this backup?')) return;
    try {
      await api.delete(`/admin/backups/${backupId}`);
      toast.success('Backup deleted');
      fetchData();
    } catch (error) {
      toast.error('Failed to delete backup');
    }
  };

  const handleDownloadBackup = async (backup) => {
    try {
      const token = localStorage.getItem('erp_token');
      window.open(`${api.defaults.baseURL}/admin/backups/${backup.id}/download?token=${token}`, '_blank');
    } catch (error) {
      toast.error('Failed to download backup');
    }
  };

  const formatBytes = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (dateStr) => {
    return new Date(dateStr).toLocaleString();
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-slate-900"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="system-admin-page">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">System Administration</h1>
          <p className="text-slate-500 mt-1">Manage backups, data reset, and system maintenance</p>
        </div>
        <Button variant="outline" onClick={fetchData}>
          <RefreshCw className="w-4 h-4 mr-2" />
          Refresh
        </Button>
      </div>

      {/* System Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Total Records</CardTitle>
            <Database className="w-4 h-4 text-slate-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{systemInfo?.total_records?.toLocaleString()}</div>
            <p className="text-xs text-slate-500 mt-1">Across all collections</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Backups</CardTitle>
            <HardDrive className="w-4 h-4 text-slate-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{systemInfo?.backup_count}</div>
            <p className="text-xs text-slate-500 mt-1">
              {formatBytes(systemInfo?.backup_storage_used_bytes || 0)} used
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Last Backup</CardTitle>
            <Clock className="w-4 h-4 text-slate-400" />
          </CardHeader>
          <CardContent>
            <div className="text-sm font-medium">
              {systemInfo?.latest_backup 
                ? formatDate(systemInfo.latest_backup.created_at)
                : 'No backups yet'}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Collection Stats */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Server className="w-5 h-5" />
            Collection Statistics
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
            {systemInfo?.collection_stats && Object.entries(systemInfo.collection_stats).map(([name, count]) => (
              <div key={name} className="p-3 bg-slate-50 rounded-lg">
                <p className="text-sm text-slate-600 capitalize">{name.replace(/_/g, ' ')}</p>
                <p className="text-xl font-bold">{count}</p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Action Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Backup Section */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileArchive className="w-5 h-5 text-blue-600" />
              Backup & Restore
            </CardTitle>
            <CardDescription>Create and manage system backups</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex gap-2">
              <Button onClick={() => setShowBackupModal(true)} data-testid="create-backup-btn">
                <HardDrive className="w-4 h-4 mr-2" />
                Create Backup
              </Button>
            </div>

            {/* Backup List */}
            <div className="border rounded-lg divide-y max-h-64 overflow-y-auto">
              {backups.length === 0 ? (
                <div className="p-4 text-center text-slate-500">
                  <FileArchive className="w-8 h-8 mx-auto mb-2 text-slate-300" />
                  <p>No backups yet</p>
                </div>
              ) : (
                backups.map((backup) => (
                  <div key={backup.id} className="p-3 hover:bg-slate-50 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      {backup.status === 'completed' ? (
                        <CheckCircle className="w-5 h-5 text-green-500" />
                      ) : backup.status === 'failed' ? (
                        <XCircle className="w-5 h-5 text-red-500" />
                      ) : (
                        <RefreshCw className="w-5 h-5 text-blue-500 animate-spin" />
                      )}
                      <div>
                        <p className="font-medium text-sm">{backup.name}</p>
                        <p className="text-xs text-slate-500">
                          {formatDate(backup.created_at)} • {formatBytes(backup.file_size || 0)}
                        </p>
                      </div>
                    </div>
                    <div className="flex gap-1">
                      {backup.status === 'completed' && (
                        <>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleDownloadBackup(backup)}
                            data-testid={`download-backup-${backup.id}`}
                          >
                            <Download className="w-4 h-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => {
                              setSelectedBackup(backup);
                              fetchRestorePreview(backup.id);
                              setShowRestoreModal(true);
                            }}
                            data-testid={`restore-backup-${backup.id}`}
                          >
                            <Upload className="w-4 h-4" />
                          </Button>
                        </>
                      )}
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDeleteBackup(backup.id)}
                        className="text-red-500 hover:text-red-600"
                        data-testid={`delete-backup-${backup.id}`}
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                ))
              )}
            </div>
          </CardContent>
        </Card>

        {/* Data Reset Section */}
        <Card className="border-red-200">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-red-700">
              <AlertTriangle className="w-5 h-5" />
              Data Reset
            </CardTitle>
            <CardDescription>Reset system data with safety controls</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <p className="text-sm text-red-700">
                <strong>Warning:</strong> Data reset operations cannot be undone. 
                A backup will be created automatically before reset.
              </p>
            </div>
            <div className="space-y-2">
              <p className="text-sm font-medium">Reset Options:</p>
              <ul className="text-sm text-slate-600 space-y-1">
                <li>• <strong>Transactional Reset:</strong> Clears orders, payments, journal entries. Keeps products, customers, accounts.</li>
                <li>• <strong>Full Reset:</strong> Clears all data except your user account and company settings.</li>
              </ul>
            </div>
            <Button 
              variant="destructive" 
              onClick={() => {
                setShowResetModal(true);
                fetchResetPreview('transactional');
              }}
              data-testid="open-reset-modal-btn"
            >
              <Trash2 className="w-4 h-4 mr-2" />
              Reset Data
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* Create Backup Modal */}
      <Dialog open={showBackupModal} onOpenChange={setShowBackupModal}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create Backup</DialogTitle>
            <DialogDescription>
              Create a full backup of all your data
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium">Backup Name (Optional)</label>
              <Input
                value={backupName}
                onChange={(e) => setBackupName(e.target.value)}
                placeholder="e.g., Before Year End"
                data-testid="backup-name-input"
              />
            </div>
            <div>
              <label className="text-sm font-medium">Description (Optional)</label>
              <Input
                value={backupDescription}
                onChange={(e) => setBackupDescription(e.target.value)}
                placeholder="e.g., Backup before financial year close"
                data-testid="backup-description-input"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowBackupModal(false)}>
              Cancel
            </Button>
            <Button onClick={handleCreateBackup} disabled={backupLoading} data-testid="confirm-backup-btn">
              {backupLoading ? (
                <>
                  <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                  Creating...
                </>
              ) : (
                <>
                  <HardDrive className="w-4 h-4 mr-2" />
                  Create Backup
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Data Reset Modal */}
      <AlertDialog open={showResetModal} onOpenChange={setShowResetModal}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle className="flex items-center gap-2 text-red-700">
              <AlertTriangle className="w-5 h-5" />
              Data Reset Confirmation
            </AlertDialogTitle>
            <AlertDialogDescription className="space-y-4">
              <div>
                <label className="text-sm font-medium mb-2 block">Reset Type</label>
                <Select value={resetType} onValueChange={handleResetTypeChange}>
                  <SelectTrigger data-testid="reset-type-select">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="transactional">Transactional Reset</SelectItem>
                    <SelectItem value="full">Full Reset</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {resetPreview && (
                <div className="bg-slate-50 rounded-lg p-3">
                  <p className="font-medium text-sm mb-2">Data to be cleared:</p>
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    {Object.entries(resetPreview.collections).map(([name, count]) => (
                      <div key={name} className="flex justify-between">
                        <span className="capitalize">{name.replace(/_/g, ' ')}</span>
                        <span className="font-medium">{count}</span>
                      </div>
                    ))}
                  </div>
                  {resetPreview.warnings?.length > 0 && (
                    <div className="mt-3 pt-3 border-t">
                      <p className="font-medium text-sm text-orange-600">Warnings:</p>
                      <ul className="text-sm text-orange-600 mt-1">
                        {resetPreview.warnings.map((w, i) => (
                          <li key={i}>• {w}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}

              <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                <p className="text-sm text-red-700 font-medium">
                  Type <strong>RESET</strong> to confirm:
                </p>
                <Input
                  value={resetConfirmation}
                  onChange={(e) => setResetConfirmation(e.target.value)}
                  className="mt-2"
                  placeholder="Type RESET"
                  data-testid="reset-confirmation-input"
                />
              </div>
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel onClick={() => setResetConfirmation('')}>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDataReset}
              disabled={resetConfirmation !== 'RESET'}
              className="bg-red-600 hover:bg-red-700"
              data-testid="confirm-reset-btn"
            >
              Reset Data
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Restore Modal */}
      <AlertDialog open={showRestoreModal} onOpenChange={setShowRestoreModal}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Restore from Backup</AlertDialogTitle>
            <AlertDialogDescription className="space-y-4">
              {selectedBackup && (
                <div className="bg-blue-50 rounded-lg p-3">
                  <p className="font-medium">{selectedBackup.name}</p>
                  <p className="text-sm text-slate-600">
                    Created: {formatDate(selectedBackup.created_at)}
                  </p>
                </div>
              )}

              {restorePreview && (
                <div className="bg-slate-50 rounded-lg p-3">
                  <p className="font-medium text-sm mb-2">Data to be restored:</p>
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    {Object.entries(restorePreview.collections).map(([name, count]) => (
                      <div key={name} className="flex justify-between">
                        <span className="capitalize">{name.replace(/_/g, ' ')}</span>
                        <span className="font-medium">{count}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div className="bg-orange-50 border border-orange-200 rounded-lg p-3">
                <p className="text-sm text-orange-700">
                  <strong>Warning:</strong> This will replace your current data with the backup data.
                  A backup of your current data will be created automatically.
                </p>
              </div>

              <div>
                <p className="text-sm font-medium">
                  Type <strong>RESTORE</strong> to confirm:
                </p>
                <Input
                  value={restoreConfirmation}
                  onChange={(e) => setRestoreConfirmation(e.target.value)}
                  className="mt-2"
                  placeholder="Type RESTORE"
                  data-testid="restore-confirmation-input"
                />
              </div>
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel onClick={() => {
              setRestoreConfirmation('');
              setSelectedBackup(null);
            }}>
              Cancel
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={handleRestore}
              disabled={restoreConfirmation !== 'RESTORE'}
              data-testid="confirm-restore-btn"
            >
              Restore Data
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
