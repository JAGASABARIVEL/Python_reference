#/usr/bin/python

import json
from pyral import Rally, RallyRESTResponse
from pyral.restapi import RALLY_REST_HEADERS

def addCollectionItems_patch(self, target, items):
    """
        Given a target which is a hydrated RallyEntity instance having a valid _type
        and a a list of hydrated Rally Entity instances (items)
        all of the same _type, construct a valid AC WSAPI collection url and
        issue a POST request to that URL supplying the item refs in an appropriate
        JSON structure as the payload.
    """
    if not items: return None
    auth_token = self.obtainSecurityToken()
    target_type = target._type
    item_types = [item._type for item in items]
    item_type = item_types[0]
    # Fix for _type in outliers
    outliers = [item for item in item_types if item != item_type]
    if outliers:
        raise RallyRESTAPIError("addCollectionItems: all items must be of the same type")
    resource = "%s/%s/%ss/add" % (target_type, target.oid, item_type)
    collection_url = '%s/%s?fetch=Name&key=%s' % (self.service_url, resource, auth_token)
    payload = {"CollectionItems":[{'_ref' : "%s/%s" % (str(item._type), str(item.oid))}
                for item in items]}
    response = self.session.post(collection_url, data=json.dumps(payload), headers=RALLY_REST_HEADERS)
    context = self.contextHelper.currentContext()
    response = RallyRESTResponse(self.session, context, resource, response, "shell", 0)
    added_items = [str(item[u'Name']) for item in response.data[u'Results']]
    return response, added_items

def repr_patch(self):
    if self.status_code == 200 and self._page:
        try:
            entity_type = self._page[0]['_type']
            return "%s result set, totalResultSetSize: %d, startIndex: %s  pageSize: %s  current Index: %s" % \
               (entity_type, self.resultCount, self.startIndex, self.pageSize, self._curIndex)
        except:
            return "%s\nErrors: %s\nWarnings: %s\nData: %s\n" % (self.status_code,
                                                                 self.errors,
                                                                 self.warnings,
                                                                 self._page)
    else:
        if self.errors:
            blurb = self.errors[0]
        elif self.warnings:
            blurb = self.warnings[0]
        else:
            # Fix for return key "Results" of self.content
            blurb = "%sResult TotalResultCount: %d  Results: %s" % \
                     (self.request_type, self.resultCount, self.content['OperationResult'])

        return "%s %s" % (self.status_code, blurb)

Rally.addCollectionItems = addCollectionItems_patch
RallyRESTResponse.__repr__ = repr_patch
