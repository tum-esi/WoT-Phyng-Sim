const mergeJsonSchemas = require('merge-json-schemas')
const json_validate = require('jsonschema').validate;

// Load TD, SD and PD schemas
const tdSchema = require('wot-thing-description-types/schema/td-json-schema-validation.json')
const baseCdSchema = require('../../schemas/base/baseCd.schema.json');
const basePdSchema = require('../../schemas/base/basePd.schema.json');

// Merge TD with SD, and TD with PD
export const cdSchema = mergeJsonSchemas([tdSchema, baseCdSchema]);
export const pdSchema = mergeJsonSchemas([tdSchema, basePdSchema]);

// Load Case specific SD and PD schemas
const chtBaseCdSchema = require('../../schemas/behavior/cht/chtBaseCd.schema.json');
const chtBasePdSchema = require('../../schemas/behavior/cht/chtBasePd.schema.json');

// Merge SD with case specific SD, and PD with case specific PD
export const chtCdSchema = mergeJsonSchemas([cdSchema, chtBaseCdSchema]);
export const chtPdSchema = mergeJsonSchemas([pdSchema, chtBasePdSchema]);

export const validateSchema = (instance: any, schema: any): void => {
    let result = json_validate(instance, schema, {nestedErrors: true});
    let err = result.toString();
    if (err) throw Error(err);
}
