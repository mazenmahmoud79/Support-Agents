import React from 'react';
import { FileUpload } from '../components/upload/FileUpload';
import './UploadPage.css';

export const UploadPage: React.FC = () => {
    return (
        <div className="upload-page">
            <h1 className="page-title">Upload Documents</h1>
            <p className="page-subtitle">
                Add documents to your AI assistant's knowledge base
            </p>

            <div className="upload-content">
                <FileUpload />
            </div>
        </div>
    );
};
