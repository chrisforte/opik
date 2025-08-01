/**
 * This file was auto-generated by Fern from our API Definition.
 */

import * as OpikApi from "../../../../index";

/**
 * @example
 *     {
 *         provider: "openai"
 *     }
 */
export interface ProviderApiKeyWrite {
    provider: OpikApi.ProviderApiKeyWriteProvider;
    apiKey?: string;
    name?: string;
    headers?: Record<string, string>;
    configuration?: Record<string, string>;
    baseUrl?: string;
}
