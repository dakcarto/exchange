from . import ExchangeTest
from elasticsearch_dsl import connections
from django.conf import settings
from elasticsearch import Elasticsearch
import pytest
from django.core.management import call_command
import subprocess


@pytest.mark.skipif(settings.ES_SEARCH is False,
                    reason="Only run if using unified search")
class GeonodeElasticsearchTest(ExchangeTest):

    def setUp(self):
        super(GeonodeElasticsearchTest, self).setUp()
        self.login()
        call_command('rebuild_index')
        # connect to the ES instance
        connections.create_connection(hosts=[settings.ES_URL])

    def test_management_commands(self):
        es = Elasticsearch(settings.ES_URL)
        mappings = es.indices.get_mapping()

        # Ensure all the indices exist in our mappings upon build
        self.assertTrue('profile-index' in mappings)
        self.assertTrue('layer-index' in mappings)
        self.assertTrue('map-index' in mappings)
        self.assertTrue('document-index' in mappings)
        self.assertTrue('group-index' in mappings)
        self.assertTrue('story-index' in mappings)

        # Call the clear command and ensure the indices have been wiped
        call_command('clear_index')
        mappings = es.indices.get_mapping()
        self.assertFalse('profile-index' in mappings)
        self.assertFalse('layer-index' in mappings)
        self.assertFalse('map-index' in mappings)
        self.assertFalse('document-index' in mappings)
        self.assertFalse('group-index' in mappings)
        self.assertFalse('story-index' in mappings)

        # Rebuild the indices and ensure they return to our mappings
        call_command('rebuild_index')
        mappings = es.indices.get_mapping()
        self.assertTrue('profile-index' in mappings)
        self.assertTrue('layer-index' in mappings)
        self.assertTrue('map-index' in mappings)
        self.assertTrue('document-index' in mappings)
        self.assertTrue('group-index' in mappings)
        self.assertTrue('story-index' in mappings)

    def test_mappings(self):
        # We only want to test mappings because the rest should be covered
        # in the views_test.py for faceting and filtering
        es = Elasticsearch(settings.ES_URL)
        mappings = es.indices.get_mapping()

        profile_mappings = mappings[
            'profile-index']['mappings']['doc']['properties']
        profile_properties = {
            "first_name": {
                "type": "text"
            },
            "id": {
                "type": "integer"
            },
            "last_name": {
                "type": "text"
            },
            "organization": {
                "type": "text"
            },
            "position": {
                "type": "keyword"
            },
            "profile": {
                "type": "keyword"
            },
            "type": {
                "fields": {
                    "english": {
                        "analyzer": "english",
                        "type": "text"
                    },
                    "text": {
                        "type": "text"
                    }
                },
                "type": "keyword"
            },
            "username": {
                "type": "text"
            }
        }
        self.assertDictEqual(profile_mappings, profile_properties)

        group_mappings = mappings[
            'group-index']['mappings']['doc']['properties']
        group_properties = {
            "description": {
                "type": "text"
            },
            "id": {
                "type": "integer"
            },
            "json": {
                "type": "text"
            },
            "title": {
                "fields": {
                    "english": {
                        "analyzer": "english",
                        "type": "text"
                    },
                    "pattern": {
                        "analyzer": "pattern_analyzer",
                        "type": "text"
                    }
                },
                "type": "text"
            },
            "title_sortable": {
                "type": "text"
            },
            "type": {
                "fields": {
                    "english": {
                        "analyzer": "english",
                        "type": "text"
                    },
                    "text": {
                        "type": "text"
                    }
                },
                "type": "keyword"
            }
        }
        self.assertDictEqual(group_mappings, group_properties)

        document_mappings = mappings[
            'document-index']['mappings']['doc']['properties']
        document_properties = {
            "abstract": {
                "fields": {
                    "english": {
                        "analyzer": "english",
                        "type": "text"
                    },
                    "pattern": {
                        "analyzer": "pattern_analyzer",
                        "type": "text"
                    }
                },
                "type": "text"
            },
            "bbox_bottom": {
                "type": "float"
            },
            "bbox_left": {
                "type": "float"
            },
            "bbox_right": {
                "type": "float"
            },
            "bbox_top": {
                "type": "float"
            },
            "category": {
                "fields": {
                    "english": {
                        "analyzer": "english",
                        "type": "text"
                    },
                    "text": {
                        "type": "text"
                    }
                },
                "type": "keyword"
            },
            "category__gn_description": {
                "type": "text"
            },
            "csw_type": {
                "type": "keyword"
            },
            "csw_wkt_geometry": {
                "type": "keyword"
            },
            "date": {
                "type": "date"
            },
            "detail_url": {
                "type": "keyword"
            },
            "id": {
                "type": "integer"
            },
            "keywords": {
                "fields": {
                    "english": {
                        "analyzer": "english",
                        "type": "text"
                    },
                    "text": {
                        "type": "text"
                    }
                },
                "type": "keyword"
            },
            "num_comments": {
                "type": "integer"
            },
            "num_ratings": {
                "type": "integer"
            },
            "owner__username": {
                "fields": {
                    "text": {
                        "type": "text"
                    }
                },
                "type": "keyword"
            },
            "popular_count": {
                "type": "integer"
            },
            "rating": {
                "type": "integer"
            },
            "regions": {
                "fields": {
                    "english": {
                        "analyzer": "english",
                        "type": "text"
                    },
                    "text": {
                        "type": "text"
                    }
                },
                "type": "keyword"
            },
            "share_count": {
                "type": "integer"
            },
            "srid": {
                "type": "keyword"
            },
            "supplemental_information": {
                "type": "text"
            },
            "temporal_extent_end": {
                "type": "date"
            },
            "temporal_extent_start": {
                "type": "date"
            },
            "thumbnail_url": {
                "type": "keyword"
            },
            "title": {
                "fields": {
                    "english": {
                        "analyzer": "english",
                        "type": "text"
                    },
                    "pattern": {
                        "analyzer": "pattern_analyzer",
                        "type": "text"
                    }
                },
                "type": "text"
            },
            "title_sortable": {
                "type": "text"
            },
            "type": {
                "fields": {
                    "english": {
                        "analyzer": "english",
                        "type": "text"
                    },
                    "text": {
                        "type": "text"
                    }
                },
                "type": "keyword"
            },
            "uuid": {
                "type": "keyword"
            }
        }
        self.assertDictEqual(document_mappings, document_properties)

        layer_mappings = mappings[
            'layer-index']['mappings']['doc']['properties']
        layer_properties = {
          "abstract" : {
            "type" : "text",
            "fields" : {
              "english" : {
                "type" : "text",
                "analyzer" : "english"
              },
              "pattern" : {
                "type" : "text",
                "analyzer" : "pattern_analyzer"
              }
            }
          },
          "bbox_bottom" : {
            "type" : "float"
          },
          "bbox_left" : {
            "type" : "float"
          },
          "bbox_right" : {
            "type" : "float"
          },
          "bbox_top" : {
            "type" : "float"
          },
          "category" : {
            "type" : "keyword",
            "fields" : {
              "english" : {
                "type" : "text",
                "analyzer" : "english"
              },
              "text" : {
                "type" : "text"
              }
            }
          },
          "category__gn_description" : {
            "type" : "text"
          },
          "csw_type" : {
            "type" : "keyword"
          },
          "csw_wkt_geometry" : {
            "type" : "keyword"
          },
          "date" : {
            "type" : "date"
          },
          "detail_url" : {
            "type" : "keyword"
          },
          "featured" : {
            "type" : "boolean"
          },
          "geogig_link" : {
            "type" : "keyword"
          },
          "has_time" : {
            "type" : "boolean"
          },
          "id" : {
            "type" : "integer"
          },
          "is_published" : {
            "type" : "boolean"
          },
          "keywords" : {
            "type" : "keyword",
            "fields" : {
              "english" : {
                "type" : "text",
                "analyzer" : "english"
              },
              "text" : {
                "type" : "text"
              }
            }
          },
          "num_comments" : {
            "type" : "integer"
          },
          "num_ratings" : {
            "type" : "integer"
          },
          "owner__first_name" : {
            "type" : "text"
          },
          "owner__last_name" : {
            "type" : "text"
          },
          "owner__username" : {
            "type" : "keyword",
            "fields" : {
              "text" : {
                "type" : "text"
              }
            }
          },
          "popular_count" : {
            "type" : "integer"
          },
          "rating" : {
            "type" : "integer"
          },
          "references" : {
            "properties" : {
              "name" : {
                "type" : "keyword",
                "fields" : {
                  "text" : {
                    "type" : "text"
                  }
                }
              },
              "scheme" : {
                "type" : "keyword",
                "fields" : {
                  "pattern" : {
                    "type" : "text",
                    "analyzer" : "pattern_analyzer"
                  },
                  "text" : {
                    "type" : "text"
                  }
                }
              },
              "url" : {
                "type" : "text"
              }
            }
          },
          "regions" : {
            "type" : "keyword",
            "fields" : {
              "english" : {
                "type" : "text",
                "analyzer" : "english"
              },
              "text" : {
                "type" : "text"
              }
            }
          },
          "share_count" : {
            "type" : "integer"
          },
          "source_host" : {
            "type" : "keyword",
            "fields" : {
              "text" : {
                "type" : "text"
              }
            }
          },
          "srid" : {
            "type" : "keyword"
          },
          "subtype" : {
            "type" : "keyword",
            "fields" : {
              "text" : {
                "type" : "text"
              }
            }
          },
          "supplemental_information" : {
            "type" : "text"
          },
          "temporal_extent_end" : {
            "type" : "date"
          },
          "temporal_extent_start" : {
            "type" : "date"
          },
          "thumbnail_url" : {
            "type" : "keyword"
          },
          "title" : {
            "type" : "text",
            "fields" : {
              "english" : {
                "type" : "text",
                "analyzer" : "english"
              },
              "pattern" : {
                "type" : "text",
                "analyzer" : "pattern_analyzer"
              }
            }
          },
          "title_sortable" : {
            "type" : "text"
          },
          "type" : {
            "type" : "keyword",
            "fields" : {
              "english" : {
                "type" : "text",
                "analyzer" : "english"
              },
              "text" : {
                "type" : "text"
              }
            }
          },
          "typename" : {
            "type" : "keyword"
          },
          "uuid" : {
            "type" : "keyword"
          }
        }
        self.assertDictEqual(layer_mappings, layer_properties)

        map_mappings = mappings[
            'map-index']['mappings']['doc']['properties']
        map_properties = {
            "abstract": {
                "fields": {
                    "english": {
                        "analyzer": "english",
                        "type": "text"
                    },
                    "pattern": {
                        "analyzer": "pattern_analyzer",
                        "type": "text"
                    }
                },
                "type": "text"
            },
            "bbox_bottom": {
                "type": "float"
            },
            "bbox_left": {
                "type": "float"
            },
            "bbox_right": {
                "type": "float"
            },
            "bbox_top": {
                "type": "float"
            },
            "category": {
                "fields": {
                    "english": {
                        "analyzer": "english",
                        "type": "text"
                    },
                    "text": {
                        "type": "text"
                    }
                },
                "type": "keyword"
            },
            "category__gn_description": {
                "type": "text"
            },
            "csw_type": {
                "type": "keyword"
            },
            "csw_wkt_geometry": {
                "type": "keyword"
            },
            "date": {
                "type": "date"
            },
            "detail_url": {
                "type": "keyword"
            },
            "id": {
                "type": "integer"
            },
            "keywords": {
                "fields": {
                    "english": {
                        "analyzer": "english",
                        "type": "text"
                    },
                    "text": {
                        "type": "text"
                    }
                },
                "type": "keyword"
            },
            "num_comments": {
                "type": "integer"
            },
            "num_ratings": {
                "type": "integer"
            },
            "owner__username": {
                "fields": {
                    "text": {
                        "type": "text"
                    }
                },
                "type": "keyword"
            },
            "popular_count": {
                "type": "integer"
            },
            "rating": {
                "type": "integer"
            },
            "regions": {
                "fields": {
                    "english": {
                        "analyzer": "english",
                        "type": "text"
                    },
                    "text": {
                        "type": "text"
                    }
                },
                "type": "keyword"
            },
            "share_count": {
                "type": "integer"
            },
            "srid": {
                "type": "keyword"
            },
            "supplemental_information": {
                "type": "text"
            },
            "temporal_extent_end": {
                "type": "date"
            },
            "temporal_extent_start": {
                "type": "date"
            },
            "thumbnail_url": {
                "type": "keyword"
            },
            "title": {
                "fields": {
                    "english": {
                        "analyzer": "english",
                        "type": "text"
                    },
                    "pattern": {
                        "analyzer": "pattern_analyzer",
                        "type": "text"
                    }
                },
                "type": "text"
            },
            "title_sortable": {
                "type": "text"
            },
            "type": {
                "fields": {
                    "english": {
                        "analyzer": "english",
                        "type": "text"
                    },
                    "text": {
                        "type": "text"
                    }
                },
                "type": "keyword"
            },
            "uuid": {
                "type": "keyword"
            }
        }
        self.assertDictEqual(map_mappings, map_properties)

        story_mappings = mappings[
            'story-index']['mappings']['doc']['properties']
        story_properties = {
            "abstract": {
                "fields": {
                    "english": {
                        "analyzer": "english",
                        "type": "text"
                    },
                    "pattern": {
                        "analyzer": "pattern_analyzer",
                        "type": "text"
                    }
                },
                "type": "text"
            },
            "bbox_bottom": {
                "type": "float"
            },
            "bbox_left": {
                "type": "float"
            },
            "bbox_right": {
                "type": "float"
            },
            "bbox_top": {
                "type": "float"
            },
            "category": {
                "fields": {
                    "english": {
                        "analyzer": "english",
                        "type": "text"
                    },
                    "text": {
                        "type": "text"
                    }
                },
                "type": "keyword"
            },
            "category__gn_description": {
                "type": "text"
            },
            "date": {
                "type": "date"
            },
            "detail_url": {
                "type": "keyword"
            },
            "distribution_description": {
                "type": "text"
            },
            "distribution_url": {
                "type": "keyword"
            },
            "featured": {
                "type": "boolean"
            },
            "id": {
                "type": "integer"
            },
            "is_published": {
                "type": "boolean"
            },
            "keywords": {
                "fields": {
                    "english": {
                        "analyzer": "english",
                        "type": "text"
                    },
                    "text": {
                        "type": "text"
                    }
                },
                "type": "keyword"
            },
            "num_chapters": {
                "type": "integer"
            },
            "num_comments": {
                "type": "integer"
            },
            "num_ratings": {
                "type": "integer"
            },
            "owner__first_name": {
                "type": "text"
            },
            "owner__last_name": {
                "type": "text"
            },
            "owner__username": {
                "fields": {
                    "text": {
                        "type": "text"
                    }
                },
                "type": "keyword"
            },
            "popular_count": {
                "type": "integer"
            },
            "rating": {
                "type": "integer"
            },
            "regions": {
                "fields": {
                    "english": {
                        "analyzer": "english",
                        "type": "text"
                    },
                    "text": {
                        "type": "text"
                    }
                },
                "type": "keyword"
            },
            "share_count": {
                "type": "integer"
            },
            "temporal_extent_end": {
                "type": "date"
            },
            "temporal_extent_start": {
                "type": "date"
            },
            "thumbnail_url": {
                "type": "keyword"
            },
            "title": {
                "fields": {
                    "english": {
                        "analyzer": "english",
                        "type": "text"
                    },
                    "pattern": {
                        "analyzer": "pattern_analyzer",
                        "type": "text"
                    }
                },
                "type": "text"
            },
            "title_sortable": {
                "type": "text"
            },
            "type": {
                "fields": {
                    "english": {
                        "analyzer": "english",
                        "type": "text"
                    },
                    "text": {
                        "type": "text"
                    }
                },
                "type": "keyword"
            },
            "uuid": {
                "type": "keyword"
            }
        }
        self.assertDictEqual(story_mappings, story_properties)
