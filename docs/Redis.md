# Redis

We will use a **persistent** instance of Redis to store values that don't make sense in the main Database. So every datapoint that doesn't have any relation to other datapoints.

## Stored information

The Redis Database will store 2 types of data.

First is the channel id of the main log pipe channel.

The Second are the email addresses that are used for verification. But not the email address itself will be saved but a hash of it. The hash will serve as a key and the value will be the amount of times the email was used to successfully verify a user and the amount of times this email address was given. The Data is stored in following way: `<hash>: "2,8"` where the email with the hash `<hash>` was used successfully twice and tried to verify 8 times.
