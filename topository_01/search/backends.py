from haystack.backends.whoosh_backend import WhooshEngine, WhooshSearchBackend


class OffsetWhooshSearchBackend(WhooshSearchBackend):
    """Keep arbitrary result slices accurate, including short final pages."""

    def search(
        self, query_string, sort_by=None, start_offset=0, end_offset=None, **kwargs
    ):
        start = start_offset or 0
        length = None if end_offset is None else end_offset - start
        # Whoosh's Haystack adapter infers page size from the slice length.
        # A final [9:15] slice consequently returns [6:12]. Fetch the prefix
        # for unaligned slices and apply the requested offset ourselves.
        unaligned = start > 0 and (
            length is None or (length > 0 and start % length != 0)
        )
        result = super().search(
            query_string,
            sort_by=sort_by,
            start_offset=0 if unaligned else start_offset,
            end_offset=end_offset,
            **kwargs,
        )
        if unaligned:
            result["results"] = result["results"][start:]
        return result


class OffsetWhooshEngine(WhooshEngine):
    backend = OffsetWhooshSearchBackend
