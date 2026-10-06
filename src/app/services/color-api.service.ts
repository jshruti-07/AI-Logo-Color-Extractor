import { Injectable } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Observable, catchError, throwError } from 'rxjs';
import {
  AnalyzeLogoResponse,
  ApiHealthResponse,
  HistoryApiResponse
} from '../models/color.model';

@Injectable({
  providedIn: 'root'
})
export class ColorApiService {
  // Uses /api via Angular dev proxy or direct fallback
  private readonly baseUrl = '/api';

  constructor(private http: HttpClient) {}

  /**
   * Health check to inspect API availability, OpenAI status, and MySQL database connection
   */
  checkHealth(): Observable<ApiHealthResponse> {
    return this.http.get<ApiHealthResponse>(`${this.baseUrl}/health`).pipe(
      catchError(this.handleError)
    );
  }

  /**
   * Uploads logo file and triggers the extraction and AI classification pipeline
   */
  analyzeLogo(file: File): Observable<AnalyzeLogoResponse> {
    const formData = new FormData();
    formData.append('file', file, file.name);

    return this.http.post<AnalyzeLogoResponse>(`${this.baseUrl}/analyze-logo`, formData).pipe(
      catchError(this.handleError)
    );
  }

  /**
   * Retrieves list of saved logo color palettes from MySQL
   */
  getHistory(limit: number = 20, offset: number = 0): Observable<HistoryApiResponse> {
    return this.http.get<HistoryApiResponse>(`${this.baseUrl}/history?limit=${limit}&offset=${offset}`).pipe(
      catchError(this.handleError)
    );
  }

  /**
   * Retrieves full details of a saved palette by ID
   */
  getPaletteById(id: number): Observable<AnalyzeLogoResponse> {
    return this.http.get<AnalyzeLogoResponse>(`${this.baseUrl}/history/${id}`).pipe(
      catchError(this.handleError)
    );
  }

  /**
   * Deletes a saved palette record from MySQL
   */
  deletePalette(id: number): Observable<{ success: boolean; message: string }> {
    return this.http.delete<{ success: boolean; message: string }>(`${this.baseUrl}/history/${id}`).pipe(
      catchError(this.handleError)
    );
  }

  private handleError(error: HttpErrorResponse): Observable<never> {
    let errorMessage = 'An unexpected error occurred. Please try again.';
    let errorCode = 'UNKNOWN_ERROR';

    if (error.error instanceof ErrorEvent) {
      // Client-side network error
      errorMessage = error.error.message || 'Network connection issue.';
      errorCode = 'CLIENT_NETWORK_ERROR';
    } else if (error.error && error.error.error) {
      // Structured backend API error
      errorMessage = error.error.error.message || errorMessage;
      errorCode = error.error.error.code || errorCode;
    } else if (error.status === 0) {
      errorMessage = 'Cannot reach backend server. Please ensure the Python FastAPI backend is running on port 8000.';
      errorCode = 'BACKEND_UNAVAILABLE';
    } else if (error.status === 413) {
      errorMessage = 'Uploaded file exceeds the maximum 5MB size limit.';
      errorCode = 'FILE_TOO_LARGE';
    } else if (error.message) {
      errorMessage = error.message;
    }

    return throwError(() => ({
      code: errorCode,
      message: errorMessage,
      status: error.status
    }));
  }
}
