const {
  CloudFrontClient,
  CreateInvalidationCommand,
} = require('@aws-sdk/client-cloudfront');

const AWS_REGION = process.env.AWS_ACCESS_KEY_ID;
const AWS_ACCESS_KEY_ID = process.env.AWS_ACCESS_KEY_ID;
const AWS_SECRET_ACCESS_KEY = process.env.AWS_SECRET_ACCESS_KEY;
const AWS_DISTRIBUTIONS_ID = process.env.AWS_DISTRIBUTIONS_ID;

const createInvalidation = async (distributionId, path) => {
  const client = new CloudFrontClient({
    region: AWS_REGION,
    credentials: {
      accessKeyId: AWS_ACCESS_KEY_ID,
      secretAccessKey: AWS_SECRET_ACCESS_KEY,
    },
  });

  const createInvalidationCommand = new CreateInvalidationCommand({
    DistributionId: distributionId,
    InvalidationBatch: {
      CallerReference: String(new Date().getTime()),
      Paths: {
        Quantity: 1,
        Items: [path],
      },
    },
  });
  const response = await client.send(createInvalidationCommand);

  console.log('Posted cloudfront invalidation, response is:');
  console.log(response);
};

createInvalidation(AWS_DISTRIBUTIONS_ID, '/*');
