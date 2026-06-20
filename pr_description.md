🎯 **What:** Fixed an SQL injection vulnerability in the `update_tweet` method of `SqliteDBDriver`. The method previously constructed the `SET` clause of the SQL `UPDATE` statement by directly joining the keys of the `fields` dictionary, allowing arbitrary SQL injection if the keys were user-controlled.

⚠️ **Risk:** An attacker who can control the `fields` dictionary keys could inject arbitrary SQL commands. This could lead to unauthorized data modification, data exfiltration, or denial of service by altering or deleting records in the database.

🛡️ **Solution:** Implemented an exact-match validation against a hardcoded whitelist of allowed columns (`album`, `body`, `platform`, `status`, `scheduled_at`, `posted_at`, `created_at`). Any attempt to pass an unlisted key will now immediately raise a `ValueError`, securely blocking SQL injection attempts while preserving all existing valid functionality.
