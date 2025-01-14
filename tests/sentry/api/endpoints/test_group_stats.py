from sentry import tsdb
from sentry.testutils import APITestCase
from sentry.testutils.silo import region_silo_test


@region_silo_test
class GroupStatsTest(APITestCase):
    def test_simple(self):
        self.login_as(user=self.user)

        group1 = self.create_group()
        group2 = self.create_group()

        url = f"/api/0/issues/{group1.id}/stats/"
        response = self.client.get(url, format="json")

        assert response.status_code == 200, response.content
        for point in response.data:
            assert point[1] == 0
        assert len(response.data) == 24

        tsdb.incr(tsdb.models.group, group1.id, count=3)
        tsdb.incr(tsdb.models.group, group2.id, count=5)

        response = self.client.get(url, format="json")

        assert response.status_code == 200, response.content
        assert response.data[-1][1] == 3, response.data
        for point in response.data[:-1]:
            assert point[1] == 0
        assert len(response.data) == 24
