from hurry.filesize import size
from flask_restful import Resource

from tools import MinioClient, MinioClientAdmin, api_tools


class ProjectAPI(api_tools.APIModeHandler):
    def get(self, project_id: int):
        project = self.module.context.rpc_manager.call.project_get_or_404(project_id=project_id)
        c = MinioClient(project)
        storage_space_quota = self.module.context.rpc_manager.call.project_get_storage_space_quota(
            project_id=project_id
            )
        buckets = c.list_bucket()
        bucket_types = {}
        total_size = 0
        for bucket in buckets:
            bucket_size = c.get_bucket_size(bucket)
            total_size += bucket_size
            response = c.get_bucket_tags(bucket)
            tags = {tag['Key']: tag['Value'] for tag in response['TagSet']} if response else {}
            if tags.get('type'):
                bucket_types[tags['type']] = bucket_types.get(tags['type'], 0) + bucket_size
        return {
            "total_bucket_size": {
                'readable': size(total_size), 
                'bytes': total_size
                },
            "system_bucket_size": {
                'readable': size(bucket_types.get("system", 0)), 
                'bytes': bucket_types.get("system", 0)
                },
            "autogenerated_bucket_size": {
                'readable': size(bucket_types.get("autogenerated", 0)), 
                'bytes': bucket_types.get("autogenerated", 0)
                },
            "local_bucket_size": {
                'readable': size(bucket_types.get("local", 0)), 
                'bytes': bucket_types.get("local", 0)
                },
            "storage_space_quota": {
                'readable': size(storage_space_quota), 
                'bytes': storage_space_quota
                },
            "free_space": {
                'readable': size(storage_space_quota - total_size), 
                'bytes': storage_space_quota - total_size
                },
            }, 200


class AdminAPI(api_tools.APIModeHandler):
    def get(self, project_id: int):
        c = MinioClientAdmin()
        buckets = c.list_bucket()
        bucket_types = {}
        total_size = 0
        for bucket in buckets:
            bucket_size = c.get_bucket_size(bucket)
            total_size += bucket_size
            response = c.get_bucket_tags(bucket)
            tags = {tag['Key']: tag['Value'] for tag in response['TagSet']} if response else {}
            if tags.get('type'):
                bucket_types[tags['type']] = bucket_types.get(tags['type'], 0) + bucket_size
        return {
            "total_bucket_size": {
                'readable': size(total_size),
                'bytes': total_size
                },
            "system_bucket_size": {
                'readable': size(bucket_types.get("system", 0)),
                'bytes': bucket_types.get("system", 0)
                },
            "autogenerated_bucket_size": {
                'readable': size(bucket_types.get("autogenerated", 0)),
                'bytes': bucket_types.get("autogenerated", 0)
                },
            "local_bucket_size": {
                'readable': size(bucket_types.get("local", 0)),
                'bytes': bucket_types.get("local", 0)
                },
            "storage_space_quota": {
                'readable': 0,
                'bytes': 0
                },
            "free_space": {
                'readable': 0,
                'bytes': 0
                },
            }, 200


class API(api_tools.APIBase):
    url_params = [
        '<string:mode>/<int:project_id>',
        '<int:project_id>',
    ]

    mode_handlers = {
        'default': ProjectAPI,
        'administration': AdminAPI
    }
