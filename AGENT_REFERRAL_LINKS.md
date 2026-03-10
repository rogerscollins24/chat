# Agent Referral Links Guide

## Overview

Each agent has a unique **referral link** that can be shared in Facebook ads, Google ads, or other marketing channels. When a client clicks your link, they're automatically assigned to you for future conversations.

## Getting Your Referral Link

### Step 1: Login to Agent Dashboard
1. Go to `http://localhost:5173/#/admin` (or your production URL)
2. Enter your email and password
3. Click "Login"

### Step 2: Find Your Referral Link
Once logged in, your referral link appears in the **green box at the top** of the left sidebar:

```
Your Referral Link
https://app-url.com/?ref_code=68WKPAJE

[Copy Link]
```

### Step 3: Copy the Link
Click the **"Copy Link"** button. It will turn green with a checkmark (✓ Copied!) to confirm the link is copied to your clipboard.

## Using Your Link in Ads

### Facebook Ads
1. Create or edit a Facebook ad campaign
2. In the **Destination URL** field, paste your referral link
3. Publish your ad
4. When clients click the ad, they'll see your chat portal and be assigned to you

### Google Ads
1. Create or edit a Google Search/Display ad
2. In the **Final URL** field, paste your referral link
3. Publish your ad
4. Clients who click will see your chat portal

### Other Platforms
You can use your referral link in any ad platform that accepts URLs:
- Instagram ads
- LinkedIn ads
- TikTok ads
- Email marketing
- Direct messages
- Website links

## How It Works (Behind the Scenes)

When a client clicks your referral link:

1. **Link Format**: `https://app-url.com/?ref_code=68WKPAJE`
   - The `ref_code` parameter contains your unique 8-character code

2. **Session Creation**: The app reads the `ref_code` and creates a new chat session
   - Your referral code is stored in the session
   - The session is automatically assigned to you

3. **Dashboard View**: You'll see the new session in your dashboard
   - Assigned sessions show "(You)" next to them
   - Messages appear in your active conversation

## Verifying Assigned Sessions

To confirm clients were assigned through your referral link:

1. **In Dashboard**: Look for sessions with "(You)" indicator in the session list
2. **Session Details**: When you select a session, you'll see:
   - Session start time
   - Client messages
   - Your agent assignment

## Important Security Notes

- **Don't share your code publicly** in places where non-clients can see it
- **Your referral code is unique** - each agent has a different code
- **No special characters** - referral codes are 8 alphanumeric characters (A-Z, 0-9)
- **Codes don't expire** - you can use the same link indefinitely

## Example Referral Link

If your referral code is `68WKPAJE`:

```
https://app-url.com/?ref_code=68WKPAJE
```

You can also add query parameters if needed:

```
https://app-url.com/?ref_code=68WKPAJE&utm_source=facebook&utm_medium=ad
```

(The `utm_` parameters are for tracking and won't interfere with the referral code)

## Troubleshooting

### My link won't copy
- Check that you're logged into the agent dashboard
- Try clicking the copy button again
- If still not working, manually select and copy the link text

### Clients aren't being assigned to me
- Verify you used the correct referral link (check for typos)
- Make sure the link includes the `ref_code=` parameter
- Check your dashboard to see if sessions appear under your name

### I need a new referral code
- Contact an administrator
- Your current code remains valid until changed
- Changing codes doesn't affect existing sessions

## Future Enhancements

As the platform grows, we may add:

- **Short URLs**: Custom branded short links (e.g., `bit.ly/leadpulse-john`)
- **QR Codes**: Scannable codes for print ads
- **Analytics**: Click-through rates, conversion tracking
- **Multiple Links**: Different links for different campaigns
- **Link Expiration**: Temporary links for limited-time offers

For now, use the simple query parameter link for maximum flexibility and zero cost.

## FAQ

**Q: Can I change my referral code?**  
A: Contact an administrator. We recommend keeping the same code for consistency across your ads.

**Q: What if someone else uses my link?**  
A: Sessions created through your link will still be assigned to you. Consider using shorter promotional periods for limited offers.

**Q: Can I see how many clients clicked my link?**  
A: Look at your session count in the dashboard. Future versions will include detailed analytics.

**Q: Do clients need to enter the code manually?**  
A: No! When they click your link, the code is automatically applied. They just see your chat portal.

**Q: Can I use the same link in multiple ads?**  
A: Yes! Use the same link across all platforms and campaigns.

---

**Last Updated**: January 2025  
**Version**: 1.0
