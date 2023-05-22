/**
 * Returns true if response status is successful.
 * @param {number} status Status code to check.
 * @return {boolean} Status successful.
 */
export const responseIsSuccessful = (status: number): boolean => {
    return ~~(status / 100) === 2;
}

/**
 * Returns true if response status is unsuccessful.
 * @param {number} status Status code to check.
 * @return {boolean} Status unsuccessful.
 */
export const responseIsUnsuccessful = (status: number): boolean => {
    return ~~(status / 100) !== 2;
}
