/**
 * Style profile constants for PseudoScribe extension
 * These define the default style profiles available in the system
 */

export interface StyleProfile {
    complexity: number;
    formality: number;
    tone: number;
    readability: number;
}

export const STYLE_PROFILES: Record<string, StyleProfile> = {
    casual: {
        complexity: 0.3,
        formality: 0.2,
        tone: 0.7,
        readability: 0.8
    },
    formal: {
        complexity: 0.7,
        formality: 0.9,
        tone: 0.4,
        readability: 0.6
    },
    technical: {
        complexity: 0.9,
        formality: 0.8,
        tone: 0.3,
        readability: 0.5
    },
    creative: {
        complexity: 0.6,
        formality: 0.3,
        tone: 0.9,
        readability: 0.7
    }
};

export type StyleProfileType = keyof typeof STYLE_PROFILES;

export function getStyleProfile(profileName: string): StyleProfile | undefined {
    return STYLE_PROFILES[profileName];
}

export function isValidStyleProfile(profileName: string): profileName is StyleProfileType {
    return profileName in STYLE_PROFILES;
}
