import urllib
import json

from exception import AddressNotFoundException, MetaDataRetrievalException

class ImageRetriever:
	META_URL = 'https://maps.googleapis.com/maps/api/streetview/metadata?'
	META_STATUS = {
		'OK': 'OK',
		'ZERO': 'ZERO_RESULTS',
		'NOT_FOUND': 'NOT_FOUND',
		'OVER_LIMIT': 'OVER_QUERY_LIMIT',
		'DENIED': 'REQUEST_DENIED',
		'INVALID': 'INVALID_REQUEST',
		'UNKNOWN': 'UNKNOWN_ERROR'
	}

	def __init__(self, targetDir, apiKey):
		self.targetDir = targetDir
		self.apiKey = apiKey

	def retrieve_images(self, locations = []):
		for loc in locations:
			try:
				meta = self.image_meta(loc);
			except AddressNotFoundException:
				# Nothing here, let's move on to the next one
				continue

	def image_meta(self, location):
		# Build the URL params
		url = self.META_URL + 'key=' + self.apiKey
		url = url + '&location=\'' + location + '\''

		response = urllib.urlopen(url)
		meta = json.loads(response.read())

		if (meta['status'] == self.META_STATUS['OK']):
			return meta
		elif (meta['status'] == self.META_STATUS['ZERO']
		      or meta.status == self.META_STATUS['NOT_FOUND']):
			# Since we're only expecting lat/long pairs and not
			# street addresses, these status values basically
			# mean the same thing
			raise AddressNotFoundException('No imagery available '
						       'for ' + location)
		else:
			raise MetaDataRetrievalException('An error occurred '
							 'retrieving address '
							 'metadata. The '
							 'error was: '
							 + meta['status'])

