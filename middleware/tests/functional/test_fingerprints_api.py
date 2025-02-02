import os
import unittest

import sqlalchemy
from flask_testing import TestCase

from middleware import create_app
from middleware.models import db
from middleware.models.fingerprint_comparison import FingerprintComparisonModel


class FingerprintComparisonTest(TestCase):
    def create_app(self):
        os.environ["APP_SETTINGS"] = "middleware.config.TestingConfig"

        app = create_app()

        return app

    def setUp(self):
        # Note: executed inside app.context
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_empty_post(self):
        pass

    def test_comparing_non_existing_video_against_nothing(self):
        response = self.client.post(
            '/api/fingerprints/comparisons',
            json=dict(
                query_video_names=['doesnotexist.avi'], reference_video_names=[],
            ),
        )

        self.assertTrue(len(response.get_json()['comparisons']) == 0)

    def test_comparing_non_existing_video_against_other_non_existing_videos(self):
        response = self.client.post(
            '/api/fingerprints/comparisons',
            json=dict(
                query_video_names=['doesnotexist.avi'],
                reference_video_names=['neitherdoesthis.avi', 'orthis.avi'],
            ),
        )

        self.assertTrue(len(response.get_json()['comparisons']) == 0)

    def test_comparing_video_against_others_that_do_not_exist(self):
        query_video_name = 'somevideo.avi'

        db.session.add(
            FingerprintComparisonModel(
                query_video_name=query_video_name,
                reference_video_name='someothervideo.avi',
                query_segment_id=1,
                reference_segment_id=1,
                match_level='LEVEL_A',
                similarity_score=1.0,
            )
        )

        db.session.commit()

        response = self.client.post(
            '/api/fingerprints/comparisons',
            json=dict(
                query_video_names=[query_video_name],
                reference_video_names=['thisdoesnotexist.avi', 'neitherddoesthis.avi'],
            ),
        )

        self.assertTrue(len(response.get_json()['comparisons']) == 0)

    def test_comparing_video_against_another_for_which_there_is_a_comparison(self):
        query_video_name = 'somevideo.avi'
        reference_video_name = 'someothervideo.avi'

        db.session.add(
            FingerprintComparisonModel(
                query_video_name=query_video_name,
                reference_video_name=reference_video_name,
                query_segment_id=1,
                reference_segment_id=1,
                match_level='LEVEL_A',
                similarity_score=1.0,
            )
        )

        db.session.commit()

        response = self.client.post(
            '/api/fingerprints/comparisons',
            json=dict(
                query_video_names=[query_video_name],
                reference_video_names=[reference_video_name],
            ),
        )

        comparison = response.get_json()['comparisons'][0]

        self.assertTrue('distinctMatches' in comparison.keys())
        self.assertEqual(1, comparison['distinctMatches'])

        self.assertTrue('totalMatches' in comparison.keys())
        self.assertEqual(1, comparison['totalMatches'])

        self.assertTrue('queryVideoName' in comparison.keys())
        self.assertEqual(query_video_name, comparison['queryVideoName'])

        self.assertTrue('referenceVideoName' in comparison.keys())
        self.assertEqual(reference_video_name, comparison['referenceVideoName'])

        self.assertTrue('numberOfQuerySegments' in comparison.keys())
        self.assertTrue('numberOfReferenceSegments' in comparison.keys())

        self.assertTrue('comparisons' in comparison.keys())
        self.assertEqual(1, len(comparison['comparisons']))

    def test_comparing_video_against_multiple_others(self):
        query_video_name = 'somevideo.avi'
        reference_video_names = ['someothervideo.avi', 'anothervideo.avi']

        for reference_video_name in reference_video_names:
            db.session.add(
                FingerprintComparisonModel(
                    query_video_name=query_video_name,
                    reference_video_name=reference_video_name,
                    query_segment_id=1,
                    reference_segment_id=1,
                    match_level='LEVEL_A',
                    similarity_score=1.0,
                )
            )

            db.session.commit()

        response = self.client.post(
            '/api/fingerprints/comparisons',
            json=dict(
                query_video_names=[query_video_name],
                reference_video_names=reference_video_names,
            ),
        )

        json_response = response.get_json()['comparisons']
        self.assertTrue(len(json_response) == 2)

    @unittest.skip("Resolved inside the services module right now...")
    def test_comparing_video_against_multiple_others_bidirectional(self):
        query_video_name = 'somevideo.avi'
        reference_video_names = ['someothervideo.avi', 'anothervideo.avi']

        for reference_video_name in reference_video_names:
            db.session.add(
                FingerprintComparisonModel(
                    query_video_name=query_video_name,
                    reference_video_name=reference_video_name,
                    query_segment_id=1,
                    reference_segment_id=1,
                    match_level='LEVEL_A',
                    similarity_score=1.0,
                )
            )

            db.session.commit()

        compare_query_video_name = reference_video_names[0]
        compare_reference_video_names = [query_video_name, reference_video_names[1]]
        response = self.client.post(
            '/api/fingerprints/comparisons',
            json=dict(
                query_video_names=[compare_query_video_name],
                reference_video_names=compare_reference_video_names,
            ),
        )

        json_response = response.get_json()
        self.assertTrue(len(json_response) == 2)

        for result in json_response:
            self.assertTrue(compare_query_video_name in result.values())

        response_reference_video_names = [
            d['reference_video_name'] for d in json_response
        ]
        self.assertEqual(compare_reference_video_names, response_reference_video_names)

    def test_unique_constraint(self):
        query_video_name = 'somevideo.avi'
        reference_video_name = 'someothervideo.avi'

        db.session.add(
            FingerprintComparisonModel(
                query_video_name=query_video_name,
                reference_video_name=reference_video_name,
                query_segment_id=1,
                reference_segment_id=1,
                match_level='LEVEL_A',
                similarity_score=1.0,
            )
        )

        db.session.commit()

        with self.assertRaises(sqlalchemy.exc.IntegrityError):
            db.session.add(
                FingerprintComparisonModel(
                    query_video_name=query_video_name,
                    reference_video_name=reference_video_name,
                    query_segment_id=1,
                    reference_segment_id=1,
                    match_level='LEVEL_A',
                    similarity_score=0.0,  # Another score
                )
            )

            db.session.commit()
