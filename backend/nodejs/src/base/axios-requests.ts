import axios, {AxiosRequestConfig, AxiosResponse} from 'axios';

/**
 * Delay for certain ms.
 * @param {number} ms Miliseconds to delay.
 * @return {Promise} Delay promise.
 */
const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

/**
 * Axios interceptor for catching error response.
 */
axios.interceptors.response.use(response => {
    return response;
}, error => {
    return error.response;
});

/**
 * Try reaching the given URL with given request for given amount of seconds.
 * @param {AxiosRequestConfig} config Request config.
 * @param {number} tries Number of tries.
 * @return {Promise<AxiosResponse>} Server response.
 * @async
 */
async function tryReaching(config: AxiosRequestConfig, tries: number): Promise<AxiosResponse> {
    for (let i = 0; i < tries; i++) {
        try {
            let response: AxiosResponse = await makeRequest(config, false);
            if (response) return response;
        } catch {
            await delay(1000);
        }
    }
    throw Error(`Host ${config.url} was not reached after ${tries} retries`)
}

/**
 * Make a request with given configuration and
 * try resending it if host is not available if needed.
 * @param {AxiosRequestConfig} config Request config.
 * @param {boolean} retry if retry is needed.
 * @return {Promise<AxiosResponse>} Server response.
 * @async
 */
export async function makeRequest(config: AxiosRequestConfig, retry: boolean = true): Promise<AxiosResponse> {
    try {
        let response = await axios.request(config);
        if (response) return response;
        throw Error(`Host ${config.url} was not reached`)
    } catch (e: any) {
        if (retry) {
            return await tryReaching(config, 5);
        }
        throw Error(e)
    }
}

/**
 * Make a GET request to given url and
 * try resending it if host is not available.
 * @param {string} url Host url.
 * @param {AxiosRequestConfig} config Request config.
 * @return {Promise<AxiosResponse>} Server response.
 * @async
 */
export async function reqGet(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse> {
    return await makeRequest({method: 'get', url, ...config});
}

/**
 * Make a POST request to given url and
 * try resending it if host is not available.
 * @param {string} url Host url.
 * @param {any} data Request data.
 * @param {AxiosRequestConfig} config Request config.
 * @return {Promise<AxiosResponse>} Server response.
 * @async
 */
export async function reqPost(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse> {
    return await makeRequest({method: 'post', data, url, ...config});
}

/**
 * Make a PUT request to given url and
 * try resending it if host is not available.
 * @param {string} url Host url.
 * @param {any} data Request data.
 * @param {AxiosRequestConfig} config Request config.
 * @return {Promise<AxiosResponse>} Server response.
 * @async
 */
export async function reqPut(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse> {
    return await makeRequest({method: 'put', data, url, ...config});
}

/**
 * Make a PATCH request to given url and
 * try resending it if host is not available.
 * @param {string} url Host url.
 * @param {any} data Request data.
 * @param {AxiosRequestConfig} config Request config.
 * @return {Promise<AxiosResponse>} Server response.
 * @async
 */
export async function reqPatch(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse> {
    return await makeRequest({method: 'patch', data, url, ...config});
}

/**
 * Make a DELETE request to given url and
 * try resending it if host is not available.
 * @param {string} url Host url.
 * @param {AxiosRequestConfig} config Request config.
 * @return {Promise<AxiosResponse>} Server response.
 * @async
 */
export async function reqDelete(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse> {
    return await makeRequest({method: 'delete', url, ...config});
}
