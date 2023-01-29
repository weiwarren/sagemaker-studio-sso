// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

const xml2js = require('xml2js');
let parseString = require("xml2js").parseString,
    stripPrefix = require("xml2js").processors.stripPrefix;
const https = require('https');
const AWS = require('aws-sdk')

exports.handler = (event, context, callback) => {
    // console.log({body: base64Decode(event.body)})
    var decodedFormData = urlDecode(base64Decode(event.body));
    var samlResponse = decodedFormData.split('&')[0];
    // console.log({samlResponse});
    var samlToken = samlResponse.split('=')[1];
    // console.log({samlToken})
    let buff = new Buffer(samlToken, 'base64');
    let samlXml = buff.toString('ascii');
    // console.log({samlXml})

    parseString(samlXml, { tagNameProcessors: [stripPrefix], preserveWhitespace: true },
        function (err, result) {
            if (err) {
                callback(null, {
                    "statusCode": 400,
                    "headers": {},
                    "body": JSON.stringify(err['message']),
                    "isBase64Encoded": false
                })
                console.error(err['message'])
            } else {
                var attrs = result.Response.Assertion[0].AttributeStatement[0].Attribute;
                console.log(attrs)
                var domainId
                var userId
                attrs.forEach(attr => {
                    switch (attr.$.Name) {
                        case 'domainid':
                            console.log('DOMAIN: ' + attr.AttributeValue[0]._)
                            domainId = attr.AttributeValue[0]._
                            break;
                        case 'username':
                            console.log('USER: ' + attr.AttributeValue[0]._)
                            userId = attr.AttributeValue[0]._
                            break;
                        default:
                            console.log(`No Match`);
                    }
                });
                var sagemaker = new AWS.SageMaker({ apiVersion: '2017-07-24' });
                var params = {
                    DomainId: domainId,
                    UserProfileName: userId
                };
                sagemaker.createUserProfile(params, (err, data) => {
                    sagemaker.createPresignedDomainUrl({ ...params, ExpiresInSeconds: 5 }, function (err, data) {
                        if (err) {
                            callback(null, {
                                "statusCode": err['statusCode'],
                                "headers": {},
                                "body": JSON.stringify(err['message']),
                                "isBase64Encoded": false
                            })
                            console.error(err['message'])
                        } else {
                            var url = data.AuthorizedUrl
                            var response = {
                                "statusCode": 302,
                                "headers": {
                                    "Location": url
                                },
                                "isBase64Encoded": false
                            };
                            callback(null, response)
                        }
                    });
                })

            }
        });

};

function base64Decode(str){
    let buff = new Buffer(str, 'base64');
    return buff.toString('ascii');
}


function urlDecode(uri) {
    return decodeURIComponent(uri.replace(/\+/g, " "));
}