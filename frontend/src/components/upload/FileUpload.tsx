import React, { useCallback, useState, useEffect, useRef } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, X, FileText, CheckCircle, XCircle, Cloud } from 'lucide-react';
import { documentService } from '../../services/documentService';
import { DocumentUploadResponse } from '../../types';
import './FileUpload.css';

interface FileUploadProps {
    onUploadComplete?: (results: DocumentUploadResponse[]) => void;
}

interface FileWithProgress {
    file: File;
    progress: number;
    status: 'pending' | 'uploading' | 'success' | 'error';
    message?: string;
    result?: DocumentUploadResponse;
}

// Global state for Google API
let gapiLoaded = false;
let gisLoaded = false;
let tokenClient: any = null;
let accessToken: string | null = null;
let pickerApiLoaded = false;

export const FileUpload: React.FC<FileUploadProps> = ({ onUploadComplete }) => {
    const [files, setFiles] = useState<FileWithProgress[]>([]);
    const [category, setCategory] = useState('');
    const [isUploading, setIsUploading] = useState(false);
    const [driveError, setDriveError] = useState<string | null>(null);
    const [isDriveLoading, setIsDriveLoading] = useState(false);
    const [isApiReady, setIsApiReady] = useState(false);
    
    const onPickCompleteRef = useRef<((files: any[]) => void) | null>(null);

    const clientId = import.meta.env.VITE_GOOGLE_DRIVE_CLIENT_ID;
    const apiKey = import.meta.env.VITE_GOOGLE_DRIVE_API_KEY;

    // Load Google APIs on component mount
    useEffect(() => {
        if (!clientId || !apiKey) {
            console.log('Google Drive credentials not configured');
            return;
        }

        // Load gapi script
        const loadGapi = () => {
            if (document.getElementById('gapi-script')) {
                return;
            }
            const script = document.createElement('script');
            script.id = 'gapi-script';
            script.src = 'https://apis.google.com/js/api.js';
            script.async = true;
            script.defer = true;
            script.onload = () => {
                (window as any).gapi.load('picker', () => {
                    console.log('✓ Google Picker API loaded');
                    pickerApiLoaded = true;
                    checkApisReady();
                });
            };
            document.body.appendChild(script);
        };

        // Load GIS (Google Identity Services) script
        const loadGis = () => {
            if (document.getElementById('gis-script')) {
                return;
            }
            const script = document.createElement('script');
            script.id = 'gis-script';
            script.src = 'https://accounts.google.com/gsi/client';
            script.async = true;
            script.defer = true;
            script.onload = () => {
                console.log('✓ Google Identity Services loaded');
                gisLoaded = true;
                initializeTokenClient();
                checkApisReady();
            };
            document.body.appendChild(script);
        };

        const initializeTokenClient = () => {
            if (!gisLoaded || tokenClient) return;
            
            tokenClient = (window as any).google.accounts.oauth2.initTokenClient({
                client_id: clientId,
                scope: 'https://www.googleapis.com/auth/drive.readonly',
                callback: (tokenResponse: any) => {
                    if (tokenResponse.access_token) {
                        console.log('✓ Access token received');
                        accessToken = tokenResponse.access_token;
                        // Open picker now that we have the token
                        createAndShowPicker();
                    } else {
                        console.error('Token response error:', tokenResponse);
                        setDriveError('Failed to authenticate with Google. Please try again.');
                        setIsDriveLoading(false);
                    }
                },
            });
            console.log('✓ Token client initialized');
        };

        const checkApisReady = () => {
            if (pickerApiLoaded && gisLoaded) {
                setIsApiReady(true);
                console.log('✓ All Google APIs ready');
            }
        };

        loadGapi();
        loadGis();
    }, [clientId, apiKey]);

    const createAndShowPicker = () => {
        if (!pickerApiLoaded || !accessToken) {
            console.error('Cannot show picker - API or token not ready');
            return;
        }

        try {
            const docsView = new (window as any).google.picker.DocsView()
                .setIncludeFolders(true)
                .setSelectFolderEnabled(false);

            const picker = new (window as any).google.picker.PickerBuilder()
                .addView(docsView)
                .addView(new (window as any).google.picker.DocsUploadView())
                .setOAuthToken(accessToken)
                .setDeveloperKey(apiKey)
                .setCallback(handlePickerCallback)
                .enableFeature((window as any).google.picker.Feature.MULTISELECT_ENABLED)
                .enableFeature((window as any).google.picker.Feature.SUPPORT_DRIVES)
                .build();

            picker.setVisible(true);
            console.log('✓ Picker displayed');
        } catch (error) {
            console.error('Error creating picker:', error);
            setDriveError('Failed to open Google Drive picker.');
            setIsDriveLoading(false);
        }
    };

    const handlePickerCallback = async (data: any) => {
        console.log('Picker callback:', data);
        
        if (data.action === (window as any).google.picker.Action.PICKED) {
            await processPickedFiles(data.docs);
        } else if (data.action === (window as any).google.picker.Action.CANCEL) {
            console.log('User cancelled picker');
            setIsDriveLoading(false);
        }
    };

    const processPickedFiles = async (driveFiles: any[]) => {
        if (!accessToken) {
            setDriveError('No access token available.');
            setIsDriveLoading(false);
            return;
        }

        const newFiles: FileWithProgress[] = [];
        let successCount = 0;
        let errorCount = 0;

        // Google Workspace file types that need export
        const googleDocsTypes: Record<string, { exportType: string; extension: string }> = {
            'application/vnd.google-apps.document': { 
                exportType: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 
                extension: '.docx' 
            },
            'application/vnd.google-apps.spreadsheet': { 
                exportType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 
                extension: '.xlsx' 
            },
            'application/vnd.google-apps.presentation': { 
                exportType: 'application/vnd.openxmlformats-officedocument.presentationml.presentation', 
                extension: '.pptx' 
            },
        };

        for (const driveFile of driveFiles) {
            try {
                console.log(`Fetching: ${driveFile.name} (${driveFile.id})`);
                console.log(`MimeType: ${driveFile.mimeType}`);

                let response: Response;
                let finalFileName = driveFile.name;
                let finalMimeType = driveFile.mimeType;

                if (googleDocsTypes[driveFile.mimeType]) {
                    // Google Workspace file - export it
                    const exportInfo = googleDocsTypes[driveFile.mimeType];
                    console.log(`Exporting as ${exportInfo.exportType}`);
                    
                    if (!finalFileName.endsWith(exportInfo.extension)) {
                        finalFileName += exportInfo.extension;
                    }
                    finalMimeType = exportInfo.exportType;

                    response = await fetch(
                        `https://www.googleapis.com/drive/v3/files/${driveFile.id}/export?mimeType=${encodeURIComponent(exportInfo.exportType)}`,
                        { headers: { Authorization: `Bearer ${accessToken}` } }
                    );
                } else {
                    // Regular file - download directly
                    response = await fetch(
                        `https://www.googleapis.com/drive/v3/files/${driveFile.id}?alt=media`,
                        { headers: { Authorization: `Bearer ${accessToken}` } }
                    );
                }

                if (!response.ok) {
                    const errorText = await response.text();
                    console.error(`Download failed (${response.status}):`, errorText);
                    throw new Error(`HTTP ${response.status}`);
                }

                const blob = await response.blob();
                const file = new File([blob], finalFileName, { 
                    type: finalMimeType || 'application/octet-stream' 
                });

                console.log(`✓ Downloaded: ${finalFileName} (${file.size} bytes)`);

                newFiles.push({
                    file,
                    progress: 0,
                    status: 'pending',
                });

                successCount++;
            } catch (error) {
                errorCount++;
                console.error(`Error downloading "${driveFile.name}":`, error);
            }
        }

        if (newFiles.length > 0) {
            setFiles((prev) => [...prev, ...newFiles]);
            console.log(`✓ Added ${successCount} file(s) from Google Drive`);
        }

        if (errorCount > 0) {
            setDriveError(
                errorCount === driveFiles.length
                    ? 'Failed to download files. Please check permissions and try again.'
                    : `${errorCount} of ${driveFiles.length} files failed to download.`
            );
        }

        setIsDriveLoading(false);
    };

    const handleDriveClick = () => {
        setDriveError(null);

        if (!clientId || !apiKey) {
            setDriveError('Google Drive is not configured.');
            return;
        }

        if (!isApiReady) {
            setDriveError('Google APIs are still loading. Please wait and try again.');
            return;
        }

        setIsDriveLoading(true);

        // If we already have a valid token, show picker directly
        if (accessToken) {
            createAndShowPicker();
        } else {
            // Request access token - this will trigger OAuth flow
            console.log('Requesting access token...');
            tokenClient.requestAccessToken({ prompt: '' });
        }
    };

    const onDrop = useCallback((acceptedFiles: File[]) => {
        const newFiles: FileWithProgress[] = acceptedFiles.map((file) => ({
            file,
            progress: 0,
            status: 'pending',
        }));
        setFiles((prev) => [...prev, ...newFiles]);
    }, []);

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop,
        accept: {
            'application/pdf': ['.pdf'],
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
            'text/plain': ['.txt'],
            'text/csv': ['.csv'],
        },
        multiple: true,
    });

    const removeFile = (index: number) => {
        setFiles((prev) => prev.filter((_, i) => i !== index));
    };

    const handleUpload = async () => {
        if (files.length === 0) return;

        setIsUploading(true);

        try {
            // Upload files
            const filesToUpload = files.map((f) => f.file);
            const results = await documentService.uploadFiles(
                filesToUpload,
                category || undefined
            );

            // Update file statuses with results
            setFiles((prev) =>
                prev.map((fileItem, index) => ({
                    ...fileItem,
                    status: results[index].status === 'completed' ? 'success' : 'error',
                    message: results[index].message,
                    result: results[index],
                    progress: 100,
                }))
            );

            if (onUploadComplete) {
                onUploadComplete(results);
            }

            // Clear successful uploads after a delay
            setTimeout(() => {
                setFiles((prev) => prev.filter((f) => f.status === 'error'));
            }, 3000);
        } catch (error) {
            console.error('Upload error:', error);
            setFiles((prev) =>
                prev.map((f) => ({
                    ...f,
                    status: 'error',
                    message: 'Upload failed',
                }))
            );
        } finally {
            setIsUploading(false);
        }
    };

    return (
        <div className="file-upload-container">
            <div className="upload-actions">
                <button
                    onClick={handleDriveClick}
                    className="btn btn-secondary google-drive-btn"
                    type="button"
                    disabled={isDriveLoading || isUploading}
                >
                    {isDriveLoading ? (
                        <>
                            <div className="spinner" style={{ width: '18px', height: '18px', marginRight: '8px' }} />
                            Loading from Drive...
                        </>
                    ) : (
                        <>
                            <Cloud size={18} className="mr-2" />
                            Select from Google Drive
                        </>
                    )}
                </button>
            </div>

            {driveError && (
                <div className="error-message" style={{ 
                    padding: '12px', 
                    marginTop: '12px',
                    backgroundColor: '#fee', 
                    border: '1px solid #fcc', 
                    borderRadius: '4px',
                    color: '#c33'
                }}>
                    <strong>Google Drive Error:</strong> {driveError}
                </div>
            )}

            <div
                {...getRootProps()}
                className={`dropzone ${isDragActive ? 'dropzone-active' : ''}`}
            >
                <input {...getInputProps()} />
                <Upload size={48} className="upload-icon" />
                <p className="dropzone-text">
                    {isDragActive
                        ? 'Drop files here...'
                        : 'Drag & drop files here, or click to select'}
                </p>
                <p className="dropzone-subtext">Supports PDF, DOCX, TXT, CSV (max 10MB)</p>
            </div>

            {files.length > 0 && (
                <div className="files-section">
                    <div className="category-input">
                        <label htmlFor="category">Category (optional):</label>
                        <input
                            id="category"
                            type="text"
                            value={category}
                            onChange={(e) => setCategory(e.target.value)}
                            placeholder="e.g., Product Documentation, FAQ"
                            disabled={isUploading}
                        />
                    </div>

                    <div className="files-list">
                        {files.map((fileItem, index) => (
                            <div key={index} className="file-item">
                                <div className="file-info">
                                    <FileText size={20} className="file-icon" />
                                    <div className="file-details">
                                        <span className="file-name">{fileItem.file.name}</span>
                                        <span className="file-size">
                                            {(fileItem.file.size / 1024).toFixed(1)} KB
                                        </span>
                                    </div>
                                </div>

                                <div className="file-status">
                                    {fileItem.status === 'success' && (
                                        <CheckCircle size={20} className="status-icon success" />
                                    )}
                                    {fileItem.status === 'error' && (
                                        <XCircle size={20} className="status-icon error" />
                                    )}
                                    {!isUploading && fileItem.status === 'pending' && (
                                        <button
                                            onClick={() => removeFile(index)}
                                            className="remove-btn"
                                            title="Remove file"
                                        >
                                            <X size={18} />
                                        </button>
                                    )}
                                </div>

                                {fileItem.message && (
                                    <p
                                        className={`file-message ${fileItem.status === 'error' ? 'error' : 'success'
                                            }`}
                                    >
                                        {fileItem.message}
                                    </p>
                                )}
                            </div>
                        ))}
                    </div>

                    <button
                        onClick={handleUpload}
                        className="btn btn-primary upload-btn"
                        disabled={isUploading}
                    >
                        {isUploading ? (
                            <>
                                <div className="spinner" />
                                Uploading...
                            </>
                        ) : (
                            <>
                                <Upload size={20} />
                                Upload {files.length} File{files.length > 1 ? 's' : ''}
                            </>
                        )}
                    </button>
                </div>
            )}
        </div>
    );
};
