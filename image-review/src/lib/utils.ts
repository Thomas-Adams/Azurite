import {clsx, type ClassValue} from 'clsx';
import {twMerge} from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export type WithoutChild<T> = T extends { child?: any } ? Omit<T, 'child'> : T;
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export type WithoutChildren<T> = T extends { children?: any } ? Omit<T, 'children'> : T;
export type WithoutChildrenOrChild<T> = WithoutChildren<WithoutChild<T>>;
export type WithElementRef<T, U extends HTMLElement = HTMLElement> = T & { ref?: U | null };

export type JsonValue = string | number | boolean | null | JsonObject | JsonValue[];
export type JsonObject = { [key: string]: JsonValue };


export interface Paginated<T> {
    page: number;
    size: number;
    total: number;
    total_pages: number;
    has_next: boolean;
    has_prev: boolean;
    params: Record<string, string | number | boolean | Date | null | undefined>;
    content: T[];
}

export interface ImageFile {
    filename: string;
    index: number;
    url: string;
    full_path: string;
    width: number;
    height: number;
    size_bytes: number;
    hash: string;
    already_reviewed: boolean;
    meta: JsonObject;
    modified_at: Date
}

export interface Review {
    rating: number;
    comment: string;
    hash: string;
    path: string;
    bucket_name: string;
}

export interface ErrorMessage {
    field?: string | null;
    message: string;
}
export interface ReviewResult {
    success: boolean;
    errors: Array<ErrorMessage>;
}


export type SortParam = 'name' | 'size' | 'date';


export function toMetaArray(meta: JsonObject): { key: string; value: JsonValue }[] {
    return Object.entries(meta).map(([key, value]) => ({key, value}));
}

export function flattenMeta(
    obj: JsonObject,
    prefix = '',
    exclude: Set<string> = new Set()
): { key: string; value: JsonValue }[] {
    return Object.entries(obj).flatMap(([key, value]) => {
        const fullKey = prefix ? `${prefix}.${key}` : key;

        if (exclude.has(key) || exclude.has(fullKey)) return [];

        if (Array.isArray(value)) {
            return value.flatMap((item, i) =>
                typeof item === 'object' && item !== null
                    ? flattenMeta(item as JsonObject, `${fullKey}[${i}]`, exclude)
                    : [{ key: `${fullKey}[${i}]`, value: item }]
            );
        }
        if (value !== null && typeof value === 'object') {
            return flattenMeta(value as JsonObject, fullKey, exclude);
        }
        return [{ key: fullKey, value }];
    });
}

export type ReviewHandler = (r: Review) => Promise<ReviewResult>;

export interface ReviewDialogProps {
    handleReview: ReviewHandler;
    imageFile: ImageFile | null
}