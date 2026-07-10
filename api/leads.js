// Vercel Serverless Function — /api/leads
// Fetches leads directly from Follow Up Boss API and returns JSON for the dashboard.
// Set FUB_API_KEY in Vercel → Project → Settings → Environment Variables.

const https = require('https');

module.exports = async (req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Cache-Control', 'no-store');

  const apiKey = process.env.FUB_API_KEY;
  if (!apiKey) {
    return res.status(500).json({ error: 'FUB_API_KEY environment variable not set in Vercel.' });
  }

  const since = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().slice(0, 19) + 'Z';
  const token = Buffer.from(`${apiKey}:`).toString('base64');

  const options = {
    hostname: 'api.followupboss.com',
    path: `/v1/people?sort=created&sortDirection=desc&limit=100&createdAfter=${encodeURIComponent(since)}`,
    headers: {
      'Authorization': `Basic ${token}`,
      'Content-Type': 'application/json',
      'X-System': 'Aaron-Dashboard',
      'X-System-Key': apiKey,
    }
  };

  try {
    const data = await new Promise((resolve, reject) => {
      https.get(options, r => {
        let body = '';
        r.on('data', c => body += c);
        r.on('end', () => {
          if (r.statusCode !== 200) reject(new Error(`FUB returned ${r.statusCode}: ${body}`));
          else resolve(JSON.parse(body));
        });
      }).on('error', reject);
    });

    const leads = (data.people || []).map(p => {
      const phones = p.phones || [];
      const emails = p.emails || [];
      const tags   = Array.isArray(p.tags) ? p.tags : [];
      const source = tags[0] || (typeof p.source === 'object' ? p.source?.name : p.source) || 'FUB';
      const assignee = typeof p.assignedTo === 'object' ? p.assignedTo?.name : '';

      return {
        id:         String(p.id || ''),
        name:       p.name || 'Unknown',
        phone:      phones[0]?.value || '',
        email:      emails[0]?.value || '',
        source,
        stage:      p.stage || 'New',
        assignedTo: assignee || '',
        receivedAt: p.created || '',
        notes:      p.lastNote || '',
        budget:     '',
      };
    });

    res.json({
      _comment:    'Live data from Follow Up Boss API via Vercel serverless function.',
      leads,
      lastUpdated: new Date().toISOString(),
      source:      'Follow Up Boss API (Vercel)',
    });

  } catch (err) {
    res.status(500).json({ error: err.message, leads: [] });
  }
};
